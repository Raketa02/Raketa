/**
 * **SAME VIBE PLAYERS on Home, the vibe sheet and See all** — walked through the real route tree
 * ([#803](https://github.com/Raketa02/Raketa/issues/803), PRD #789; ADR-0204 §6; the Home rows screens
 * §6, §8; the mechanics §8, §11–§13; the words §31.8, §31.10).
 *
 * - **The row**: fourth of the five, *See all ›* named; gone when the read holds nobody, or fails.
 * - **A tile**: the face, the nickname, the vibe %, *6 things in common*, the tint; the shared tags
 *   fitted to three lines with *+N more* — **measured**, so the suite lays the chips out as a screen
 *   would and reads what is drawn; the round button asking from the row.
 * - **The vibe sheet**: *You and …*, the worded button, the identity row, every photo, the intro, every
 *   tag with the shared ones reading *· you too*; the face opening the record over it, its requests
 *   found through *same vibe*; the record's refusal.
 * - **See all**: pushed over Home with the tab lit, the two columns, the pill — *All* and the served
 *   sports — a sport re-reading with it, paging, and the empty line.
 * - **The request card** on the receiver's Home reads *6 things in common*, or its fallback.
 *
 * **The routes are answered by a small fake of the server** (`vibeServer`): a write moves the person's
 * relation, and See all keeps who holds a level in a sport it is asked for.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { FlatList } from 'react-native';

import { FRIENDS_COPY, roundLabel } from '@/features/friends/types';
import { RECORD_UNAVAILABLE } from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { socialTagChip, socialTagLabel } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import {
  SAME_VIBE_ALL_PATH,
  SAME_VIBE_PATH,
  launchSignedIn,
  stubGate,
  stubHome,
  stubNewInRaketa,
} from '@/test-support/onboardingRouter';
import { openNeedsYourAnswer } from '@/test-support/needsYourAnswer';
import { servedReliability } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { rereadDiscovery } from '../hooks/useNewInRaketa';

import { DISCOVERY_COPY, moreTags, nobodySharesYourTagsIn } from './discoveryCopy';

const COPY = DISCOVERY_COPY.sameVibe;
const HIDDEN = { includeHiddenElements: true } as const;

/** The vibe % the server sends for each count — 1 − ½ⁿ, rounded (the mechanics §8.2). */
const VIBE: Readonly<Record<number, number>> = { 1: 50, 2: 75, 3: 88, 4: 94, 5: 97, 6: 98 };

type Held = { readonly tags: readonly SocialTagId[]; readonly sports?: readonly Wire['Sport'][] };

const vibe = (
  n: number,
  nickname: string,
  shared: readonly SocialTagId[],
  relation: Wire['FriendRelation'] = 'NONE',
): Wire['SameVibePlayerSchema'] => ({
  player_id: `e0000000-0000-4000-8000-0000000007${String(n).padStart(2, '0')}`,
  nickname,
  photo_id: null,
  photo_url: null,
  vibe_percent: VIBE[shared.length]!,
  in_common: shared.length,
  shared_tags: [...shared],
  relation,
});

const SIX: readonly SocialTagId[] = [
  'STAYS_FOR_A_DRINK',
  'SETTLES_UP_ON_THE_SPOT',
  'BOOKS_THE_NEXT_ONE',
  'PLAYS_TO_WIN',
  'LAUGHS_OFF_MISTAKES',
  'HERE_TO_IMPROVE',
];

/** Karol — a friend, all six of the reader's tags: 98%. */
const KAROL = vibe(1, 'karol.t', SIX, 'FRIEND');
/** Kuba — a stranger, two in common: 75%, **+**. */
const KUBA = vibe(2, 'kuba.w', ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN']);
/** Ania — asked the reader, one in common: 50%, *1 thing in common*. */
const ANIA = vibe(3, 'ania.k', ['HERE_TO_IMPROVE'], 'ASKED_YOU');

const ROW = [KAROL, KUBA, ANIA];

/** What each holds beyond the tags they share — the record's own tags, and the sports See all keeps. */
const HOLDS: Readonly<Record<string, Held>> = {
  [KAROL.player_id]: { tags: [...SIX], sports: ['PADEL', 'TENNIS'] },
  [KUBA.player_id]: {
    tags: ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN', 'QUIET_AND_FOCUSED'],
    sports: ['TENNIS'],
  },
  [ANIA.player_id]: { tags: ['HERE_TO_IMPROVE', 'SHARES_A_LIFT'] },
};

const KAROL_PHOTOS: Wire['RecordPhotoSchema'][] = [
  { photo_id: 'f-karol-1', photo_url: 'https://photos.example/karol-1.jpg' },
  { photo_id: 'f-karol-2', photo_url: 'https://photos.example/karol-2.jpg' },
];

const JOINER: Wire['NewInRaketaPlayerSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000000999',
  nickname: 'ola.n',
  photo_id: null,
  photo_url: null,
  joined_at: '2026-11-13T10:00:00Z',
  days_since_joined: 1,
  sports: [],
  relation: 'NONE',
};

const REQUESTS_PATH = '/api/v1/friends/requests';
const recordPath = (id: string) => `/api/v1/players/${id}/record`;

let transport: Transport;

/**
 * **The Same vibe routes, faked** — the row and See all read each person's relation as the writes
 * left it; See all pages by `after`, and **a sport keeps who holds a level in it**.
 */
function vibeServer(
  initially: readonly Wire['SameVibePlayerSchema'][] = ROW,
  { pageSize = 20 }: { readonly pageSize?: number } = {},
) {
  let people = [...initially];
  const relationOf = (id: string) => people.find((one) => one.player_id === id)?.relation;
  const sportsOf = (id: string) => HOLDS[id]?.sports ?? [];

  stubGate(transport, { hasPlayerProfile: true });
  transport.on('GET', SAME_VIBE_PATH, () =>
    json<Wire['SameVibeResponse']>({ players: [...people] }),
  );
  transport.on('GET', SAME_VIBE_ALL_PATH, (request) => {
    const query = new URLSearchParams(request.path.split('?')[1] ?? '');
    const sport = query.get('sport') as Wire['Sport'] | null;
    const kept =
      sport === null ? people : people.filter((one) => sportsOf(one.player_id).includes(sport));
    const from = Number(query.get('after') ?? '0');
    return json<Wire['SameVibePageResponse']>({
      players: kept.slice(from, from + pageSize),
      next: from + pageSize < kept.length ? String(from + pageSize) : null,
      sports: (['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'] as const).filter((each) =>
        people.some((one) => sportsOf(one.player_id).includes(each)),
      ),
    });
  });
  transport.on('POST', REQUESTS_PATH, (request) => {
    const { player_id: id } = request.body as Wire['AskToBeFriendsRequest'];
    const relation = relationOf(id) === 'ASKED_YOU' ? 'FRIEND' : 'SENT';
    people = people.map((one) => (one.player_id === id ? { ...one, relation } : one));
    return json<Wire['RelationResponse']>({ relation });
  });
  for (const one of initially) {
    transport.on('GET', recordPath(one.player_id), () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: relationOf(one.player_id) ?? 'NONE',
        can_add_friend: relationOf(one.player_id) === 'NONE',
        nickname: one.nickname,
        photos: one.player_id === KAROL.player_id ? KAROL_PHOTOS : [],
        // Karol's face is his first photo, and he wrote an intro; the others have neither.
        ...(one.player_id === KAROL.player_id
          ? {
              photo_id: 'f-karol-1',
              photo_url: KAROL_PHOTOS[0]!.photo_url,
              intro: 'Moved from Wrocław in May. Needs opponents.',
            }
          : {}),
        area_code: 'A+050612+0019938',
        social_tags: [...(HOLDS[one.player_id]?.tags ?? one.shared_tags)],
        sports: [],
        reliability: servedReliability({ player_score: 100, is_new: true }),
      }),
    );
  }
}

beforeEach(() => {
  transport = installTransport();
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
  resetSessionStatus();
  await clearStoredTokens();
});

const tile = (person: Wire['SameVibePlayerSchema']) =>
  within(screen.getByTestId(`same-vibe-${person.player_id}`));
const round = (person: Wire['SameVibePlayerSchema'], relation: Wire['FriendRelation']) =>
  screen.findByRole('button', { name: roundLabel(relation, person.nickname) });
const rowReads = () => transport.requestsTo('GET', SAME_VIBE_PATH).length;
/** The row's tiles, as drawn, left to right. */
const tileIds = () =>
  screen
    .getAllByTestId(/^same-vibe-e0/)
    .map((node) => (node.props.testID as string).replace('same-vibe-', ''));
const pageReads = () => transport.requestsTo('GET', SAME_VIBE_ALL_PATH);
const asked = () => transport.requestsTo('POST', REQUESTS_PATH).map((request) => request.body);
const sheets = () => screen.queryAllByTestId('bottom-sheet');
const vibeSheet = () => within(sheets()[0]!);

/** The section headings Home draws, top to bottom. */
const headings = () =>
  screen
    .getAllByRole('header')
    .map((node) => node.props.children as string)
    .filter((text) => typeof text === 'string');

async function homeWithTheRow() {
  await launchSignedIn();
  await screen.findByRole('header', { name: COPY.heading });
}

/** Opens the person's vibe sheet from their tile, and waits for the record it reads. */
async function openSheet(person: Wire['SameVibePlayerSchema']) {
  fireEvent.press(
    within(screen.getByTestId(`same-vibe-${person.player_id}`)).getAllByRole('button')[0]!,
  );
  await waitFor(() => expect(sheets()).toHaveLength(1));
  await vibeSheet().findByTestId('vibe-face');
}

/**
 * **Lays a tile's chips out as a screen would** — the line `lineWidth` wide, each chip `chipWidth`
 * and each *+N more* `moreWidth` — the layout a device reports on its own.
 */
function layOut(
  person: Wire['SameVibePlayerSchema'],
  { lineWidth, chipWidth, moreWidth }: Record<'lineWidth' | 'chipWidth' | 'moreWidth', number>,
) {
  const one = tile(person);
  const layout = (width: number) => ({
    nativeEvent: { layout: { x: 0, y: 0, width, height: 18 } },
  });
  fireEvent(one.getByTestId('shared-tags'), 'layout', layout(lineWidth));
  for (const node of one.getAllByTestId(/^measure-tag-/, HIDDEN)) {
    fireEvent(node, 'layout', layout(chipWidth));
  }
  for (const node of one.queryAllByTestId(/^measure-more-/, HIDDEN)) {
    fireEvent(node, 'layout', layout(moreWidth));
  }
}

describe('the row on Home', () => {
  it('stands fourth of the five — after New in Raketa — with See all named', async () => {
    vibeServer();
    stubNewInRaketa(transport, [JOINER]);
    await homeWithTheRow();
    await screen.findByRole('header', { name: DISCOVERY_COPY.newInRaketa.heading });

    const order = headings();
    const joiners = order.indexOf(DISCOVERY_COPY.newInRaketa.heading);
    expect(order[joiners + 1]).toBe(COPY.heading);
    expect(
      within(screen.getByTestId('same-vibe')).getByRole('link', { name: COPY.seeAllLabel }),
    ).toBeTruthy();
  });

  it('draws the tiles in the read’s order', async () => {
    vibeServer();
    await homeWithTheRow();

    expect(tileIds()).toEqual(ROW.map((one) => one.player_id));
  });

  it('is gone with its heading while the read holds nobody', async () => {
    vibeServer([]);
    await launchSignedIn();

    await waitFor(() => expect(rowReads()).toBeGreaterThan(0));
    await screen.findByText(/^Your games/);
    expect(screen.queryByRole('header', { name: COPY.heading })).toBeNull();
  });

  it('is left out when its read fails, and the rest of Home stands', async () => {
    vibeServer();
    transport.on('GET', SAME_VIBE_PATH, () => errorResponse(503, 'block_state_unavailable'));
    await launchSignedIn();

    await waitFor(() => expect(rowReads()).toBeGreaterThan(0));
    expect(await screen.findByText(/^Your games/)).toBeTruthy();
    expect(screen.queryByRole('header', { name: COPY.heading })).toBeNull();
  });
});

describe('a tile', () => {
  it('draws the nickname, the vibe %, and how many things the two have in common', async () => {
    vibeServer();
    await homeWithTheRow();

    expect(tile(KAROL).getByText('karol.t')).toBeTruthy();
    expect(tile(KAROL).getByText('98%')).toBeTruthy();
    expect(tile(KAROL).getByText('6 things in common')).toBeTruthy();
    expect(tile(KUBA).getByText('75%')).toBeTruthy();
    expect(tile(KUBA).getByText('2 things in common')).toBeTruthy();
    expect(tile(ANIA).getByText('50%')).toBeTruthy();
    expect(tile(ANIA).getByText('1 thing in common')).toBeTruthy();
  });

  it('is washed in the poster’s hue, and speaks who, the %, the count and every tag shared', async () => {
    vibeServer();
    await homeWithTheRow();

    expect(tile(KUBA).getByTestId('tinted-tile-tint', HIDDEN)).toBeTruthy();
    expect(
      screen.getByRole('button', {
        name: 'kuba.w, 75%, 2 things in common: Stays for a drink, Plays to win',
      }),
    ).toBeTruthy();
  });

  it('draws no chip until the line and every chip are measured', async () => {
    vibeServer();
    await homeWithTheRow();

    expect(tile(KUBA).queryByText(socialTagLabel('PLAYS_TO_WIN'))).toBeNull();
  });

  it('draws every chip that fits in three lines, and none of +N more when all of them fit', async () => {
    vibeServer();
    await homeWithTheRow();

    // Two to a line: 60 · 60 in 130.
    layOut(KUBA, { lineWidth: 130, chipWidth: 60, moreWidth: 40 });

    expect(tile(KUBA).getByText(socialTagLabel('STAYS_FOR_A_DRINK'))).toBeTruthy();
    expect(tile(KUBA).getByText(socialTagLabel('PLAYS_TO_WIN'))).toBeTruthy();
    expect(tile(KUBA).queryByText(/more$/)).toBeNull();
  });

  it('caps the chips at three lines, the last place a +N more for the rest', async () => {
    vibeServer();
    await homeWithTheRow();

    // One to a line in 130 (70 + 6 + 70 = 146): 70 | 70 | 70 · +3 more (70 + 6 + 40 = 116).
    layOut(KAROL, { lineWidth: 130, chipWidth: 70, moreWidth: 40 });

    const drawn = SIX.filter((id) => tile(KAROL).queryByText(socialTagLabel(id)) !== null);
    expect(drawn).toEqual(SIX.slice(0, 3));
    expect(tile(KAROL).getByText(moreTags(3))).toBeTruthy();
  });

  it('gives up a chip where the count would not fit beside it, and counts one more', async () => {
    vibeServer();
    await homeWithTheRow();

    // One to a line in 100: 60 · +3 more would be 107, so the third chip gives way to +4 more.
    layOut(KAROL, { lineWidth: 100, chipWidth: 60, moreWidth: 41 });

    const drawn = SIX.filter((id) => tile(KAROL).queryByText(socialTagLabel(id)) !== null);
    expect(drawn).toEqual(SIX.slice(0, 2));
    expect(tile(KAROL).getByText(moreTags(4))).toBeTruthy();
  });

  it('asks from the row naming neither a group nor a sport', async () => {
    vibeServer();
    await homeWithTheRow();

    fireEvent.press(await round(KUBA, 'NONE'));

    await waitFor(() =>
      expect(asked()).toEqual([{ player_id: KUBA.player_id, made_from: 'SAME_VIBE' }]),
    );
    expect(await round(KUBA, 'SENT')).toBeTruthy();
  });

  it('holds the tile where it was, reading request sent, though the next read moves it', async () => {
    vibeServer();
    await homeWithTheRow();
    const drawn = tileIds();
    const before = rowReads();
    // §9.1 on every read: asking Kuba makes him a gap, and a fresh match behind him takes his place.
    const ZOSIA = vibe(4, 'zosia.p', ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN', 'HERE_TO_IMPROVE']);
    transport.on('POST', REQUESTS_PATH, () => {
      transport.on('GET', SAME_VIBE_PATH, () =>
        json<Wire['SameVibeResponse']>({ players: [ZOSIA, KAROL, ANIA] }),
      );
      return json<Wire['RelationResponse']>({ relation: 'SENT' });
    });

    fireEvent.press(await round(KUBA, 'NONE'));
    await waitFor(() => expect(asked()).toHaveLength(1));
    // Once the write has settled …
    await waitFor(() => expect(queryClient.isMutating() + queryClient.isFetching()).toBe(0));

    // … the tile is where it was, reading … : the row under the thumb never moves.
    expect(tileIds()).toEqual(drawn);
    expect(screen.getByRole('button', { name: roundLabel('SENT', 'kuba.w') })).toBeTruthy();
    expect(rowReads()).toBe(before);

    // The next read — a pull, a return to Home — works §9.1 out again, and he has gone.
    await act(() => rereadDiscovery(queryClient));
    await waitFor(() =>
      expect(tileIds()).toEqual([ZOSIA, KAROL, ANIA].map((one) => one.player_id)),
    );
  });
});

describe('the vibe sheet', () => {
  it('opens on a tile: You and them, the worded button, the face, the count, and the record’s line', async () => {
    vibeServer();
    await homeWithTheRow();

    await openSheet(KAROL);

    const shown = vibeSheet();
    expect(shown.getByText('You and karol.t')).toBeTruthy();
    expect(shown.getByRole('button', { name: roundLabel('FRIEND', 'karol.t') })).toBeTruthy();
    expect(shown.getByText(FRIENDS_COPY.round.worded.FRIEND)).toBeTruthy();
    expect(shown.getByRole('button', { name: 'karol.t' })).toBeTruthy();
    // The record writes no distance from Home, so the count stands alone.
    expect(shown.getByText('6 things in common')).toBeTruthy();
  });

  it('draws every photo, the intro in its marks, and every tag — the shared ones reading you too', async () => {
    vibeServer();
    await homeWithTheRow();

    await openSheet(KAROL);
    const shown = vibeSheet();
    expect(shown.getByTestId('carousel-photo-f-karol-1', HIDDEN)).toBeTruthy();
    expect(shown.getByTestId('carousel-photo-f-karol-2', HIDDEN)).toBeTruthy();
    expect(shown.getByText('“Moved from Wrocław in May. Needs opponents.”')).toBeTruthy();
    for (const id of SIX) {
      expect(shown.getByText(socialTagChip({ id, shared: true }))).toBeTruthy();
    }
  });

  it('draws their other tags plain beside the shared ones, and no carousel with no photo', async () => {
    vibeServer();
    await homeWithTheRow();

    await openSheet(KUBA);
    const shown = vibeSheet();
    expect(shown.getByText(socialTagChip({ id: 'PLAYS_TO_WIN', shared: true }))).toBeTruthy();
    expect(shown.getByText(socialTagChip({ id: 'QUIET_AND_FOCUSED', shared: false }))).toBeTruthy();
    expect(shown.queryByTestId('vibe-photos', HIDDEN)).toBeNull();
  });

  it('its worded button asks from the row, and moves with the row’s read', async () => {
    vibeServer();
    await homeWithTheRow();

    await openSheet(KUBA);
    fireEvent.press(vibeSheet().getByRole('button', { name: roundLabel('NONE', 'kuba.w') }));

    await waitFor(() =>
      expect(asked()).toEqual([{ player_id: KUBA.player_id, made_from: 'SAME_VIBE' }]),
    );
    expect(
      await vibeSheet().findByRole('button', { name: roundLabel('SENT', 'kuba.w') }),
    ).toBeTruthy();
  });

  it('opens the full record over itself from the face, whose request is found through same vibe', async () => {
    vibeServer();
    await homeWithTheRow();

    await openSheet(KUBA);
    fireEvent.press(vibeSheet().getByRole('button', { name: 'kuba.w' }));

    await waitFor(() => expect(sheets()).toHaveLength(2));
    const record = within(sheets()[1]!);
    fireEvent.press(await record.findByRole('button', { name: FRIENDS_COPY.record.add }));

    await waitFor(() =>
      expect(asked()).toEqual([{ player_id: KUBA.player_id, made_from: 'SAME_VIBE' }]),
    );
  });

  it('stays up with the record over it when a write there would move them, and closes once a read does', async () => {
    vibeServer();
    await homeWithTheRow();
    // Asking Kuba from his record makes him a gap, and a fresh match takes his place among the ten.
    transport.on('POST', REQUESTS_PATH, () => {
      transport.on('GET', SAME_VIBE_PATH, () =>
        json<Wire['SameVibeResponse']>({ players: [KAROL, ANIA] }),
      );
      return json<Wire['RelationResponse']>({ relation: 'SENT' });
    });

    await openSheet(KUBA);
    fireEvent.press(vibeSheet().getByRole('button', { name: 'kuba.w' }));
    await waitFor(() => expect(sheets()).toHaveLength(2));
    fireEvent.press(
      await within(sheets()[1]!).findByRole('button', { name: FRIENDS_COPY.record.add }),
    );

    // The row holds still under both sheets, his sheet reading the answer.
    expect(
      await vibeSheet().findByRole('button', { name: roundLabel('SENT', 'kuba.w') }),
    ).toBeTruthy();
    expect(sheets()).toHaveLength(2);

    // The next read — the app foregrounded with them up — works §9.1 out again: he has gone.
    await act(() => rereadDiscovery(queryClient));
    await waitFor(() => expect(screen.queryByTestId(`same-vibe-${KUBA.player_id}`)).toBeNull());
    await waitFor(() => expect(sheets()).toHaveLength(0));

    await openSheet(ANIA);
    expect(sheets()).toHaveLength(1);
    expect(vibeSheet().getByText('You and ania.k')).toBeTruthy();
  });

  it('says the record’s refusal, and nothing else, where the record does not open', async () => {
    vibeServer();
    transport.on('GET', recordPath(KUBA.player_id), () => errorResponse(404, 'record_unavailable'));
    await homeWithTheRow();

    fireEvent.press(
      within(screen.getByTestId(`same-vibe-${KUBA.player_id}`)).getAllByRole('button')[0]!,
    );

    expect(await vibeSheet().findByText(RECORD_UNAVAILABLE)).toBeTruthy();
    expect(vibeSheet().queryByTestId('vibe-face')).toBeNull();
  });
});

// The request waits in Needs your answer since #816, and its tile says no found-by line (ADR-0205 §1):
// where it was found is still served, and drawn nowhere.
describe('a request from Same vibe, in Needs your answer', () => {
  const request = (
    over: Partial<Wire['HomeFriendRequestSchema']>,
  ): Wire['HomeFriendRequestSchema'] => ({
    player_id: ANIA.player_id,
    nickname: ANIA.nickname,
    photo_id: null,
    photo_url: null,
    asked_at: '2026-11-13T07:00:00Z',
    by_link: false,
    from_ranking: false,
    from_new_players: false,
    from_same_level: false,
    from_same_vibe: true,
    group: null,
    sport: null,
    level: null,
    player_score: 100,
    reliability_band: 'VERY_HIGH',
    percent_even: null,
    in_common: 6,
    ...over,
  });

  // The row holds Kuba alone, so no tile on it says Ania's count.
  it('says no line of where it was found, today’s things in common included', async () => {
    vibeServer([KUBA]);
    stubHome(transport, { friend_requests: [request({})] });
    await homeWithTheRow();
    await openNeedsYourAnswer();

    // Kuba's tile on the row under the sheet says his own; the sheet says none.
    const sheet = within(screen.getByTestId('bottom-sheet'));
    expect(sheet.getByTestId(`friend-request-${ANIA.player_id}`)).toBeTruthy();
    expect(sheet.queryByText(/things? in common/)).toBeNull();
    expect(sheet.queryByText(/Found you through your tags/)).toBeNull();
  });
});

describe('See all', () => {
  async function openSeeAll() {
    await homeWithTheRow();
    fireEvent.press(screen.getByRole('link', { name: COPY.seeAllLabel }));
    await waitFor(() => expect(screen).toHavePathname('/same-vibe'));
    await screen.findByTestId('same-vibe-grid');
  }
  const listed = () =>
    within(screen.getByTestId('same-vibe-grid'))
      .getAllByTestId(/^same-vibe-e0/)
      .map((node) => (node.props.testID as string).replace('same-vibe-', ''));

  it('is pushed over Home, the tab still lit, titled with the pill on All', async () => {
    vibeServer();
    await openSeeAll();

    expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();
    expect(screen.getByText(COPY.title)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sport: All' })).toBeTruthy();
  });

  it('draws the tiles two to a line, in the read’s order, each opening the same sheet', async () => {
    vibeServer();
    await openSeeAll();

    expect(screen.UNSAFE_getByType(FlatList).props.numColumns).toBe(2);
    expect(listed()).toEqual(ROW.map((one) => one.player_id));

    fireEvent.press(
      within(
        within(screen.getByTestId('same-vibe-grid')).getByTestId(`same-vibe-${KUBA.player_id}`),
      ).getAllByRole('button')[0]!,
    );
    expect(await vibeSheet().findByText('You and kuba.w')).toBeTruthy();
  });

  it('offers All and the sports served; a sport re-reads with it and keeps who holds a level there', async () => {
    vibeServer();
    await openSeeAll();

    fireEvent.press(screen.getByRole('button', { name: 'Sport: All' }));
    const bar = within(screen.getByTestId('sport-bar'));
    expect(
      bar.getAllByRole('button').map((option) => option.props.accessibilityLabel as string),
    ).toEqual(['Padel', 'Tennis', 'All']);

    fireEvent.press(bar.getByRole('button', { name: 'Tennis' }));
    await waitFor(() => expect(pageReads().at(-1)!.path).toContain('sport=TENNIS'));
    await waitFor(() => expect(listed()).toEqual([KAROL.player_id, KUBA.player_id]));
  });

  it('reads the next page as the grid nears its end, and never twice', async () => {
    const many = Array.from({ length: 6 }, (_, at) =>
      vibe(20 + at, `vibe.${at}`, ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE']),
    );
    vibeServer(many, { pageSize: 4 });
    await openSeeAll();
    expect(pageReads()).toHaveLength(1);
    expect(listed()).toHaveLength(4);

    fireEvent(screen.UNSAFE_getByType(FlatList), 'endReached');
    fireEvent(screen.UNSAFE_getByType(FlatList), 'endReached');

    await waitFor(() => expect(pageReads()).toHaveLength(2));
    expect(pageReads()[1]!.path).toContain('after=4');
    await waitFor(() => expect(listed()).toHaveLength(6));
    fireEvent(screen.UNSAFE_getByType(FlatList), 'endReached');
    expect(pageReads()).toHaveLength(2);
  });

  it('says so when a sport leaves nobody', async () => {
    vibeServer();
    await openSeeAll();
    transport.on('GET', SAME_VIBE_ALL_PATH, () =>
      json<Wire['SameVibePageResponse']>({ players: [], next: null, sports: ['PADEL'] }),
    );

    fireEvent.press(screen.getByRole('button', { name: 'Sport: All' }));
    fireEvent.press(within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Padel' }));

    expect(await screen.findByText(nobodySharesYourTagsIn('padel'))).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sport: Padel' })).toBeTruthy();
  });
});
