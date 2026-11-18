/**
 * **Players at your level on Home, the comparison sheet and See all** — FOR YOU's second line, walked
 * through the real route tree ([#802](https://github.com/Raketa02/Raketa/issues/802), PRD #789;
 * [#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0204 §4, ADR-0205 §5; the Home rows
 * screens §4; the mechanics §6, §11–§13; the words §31.5, §31.6, §31.10).
 *
 * - **The line**: second of the five, closed; open, its cards and *See all ›* named at its foot; hidden
 *   without a level, or when its read fails.
 * - **A card**: You and them, both levels, the % in the game cards' colours, *EVEN*, the sport; the gap
 *   in words; *N sports ›* only above one; the face opening the record, its requests found at the
 *   card's sport; the round button asking from the row.
 * - **The comparison sheet**: *You vs …*, the worded button, one block per shared sport in the served
 *   order, each tag in the light version of its colour.
 * - **See all**: pushed over Home with the tab lit, the pill — *All* and the served sports — a sport
 *   re-reading with it, paging, and the empty line.
 * - **The request card** on the receiver's Home reads *Your level in padel · 91% even*, or its
 *   fallback.
 *
 * **The routes are answered by a small fake of the server** (`levelServer`): a write moves the
 * person's relation, and See all compares everybody in a sport it is asked for — so what a card draws
 * after a write is the read again, never this client guessing.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { FlatList, StyleSheet, type TextStyle } from 'react-native';

import { FRIENDS_COPY, roundLabel } from '@/features/friends/types';
import { GROUPS_COPY } from '@/features/groups/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import { isOpen, lineTitles, openLine } from '@/test-support/forYou';
import {
  SAME_LEVEL_ALL_PATH,
  SAME_LEVEL_PATH,
  launchSignedIn,
  stubGate,
  stubHome,
  stubHottestGroups,
  stubNewInRaketa,
  stubOwnRecord,
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

import { DISCOVERY_COPY, nobodyToCompareIn } from './discoveryCopy';

const COPY = DISCOVERY_COPY.sameLevel;

const comparison = (
  sport: Wire['Sport'],
  over: Partial<Wire['SameLevelSportSchema']> = {},
): Wire['SameLevelSportSchema'] => ({
  sport,
  your_level: 2.71,
  their_level: 2.69,
  percent_even: 91,
  level_gap: -0.02,
  your_band: { name: 'Established', lower: 2.65, upper: 3.85 },
  ...over,
});

const player = (
  n: number,
  nickname: string,
  sports: readonly Wire['SameLevelSportSchema'][],
  relation: Wire['FriendRelation'] = 'NONE',
): Wire['SameLevelPlayerSchema'] => ({
  player_id: `e0000000-0000-4000-8000-0000000009${String(n).padStart(2, '0')}`,
  nickname,
  photo_id: null,
  photo_url: null,
  shown: sports[0]!,
  sports: [...sports],
  relation,
});

/** Zofia — a friend, 91% in padel and 51% in squash: green, *0,02 below you*, *2 sports ›*. */
const ZOFIA = player(
  1,
  'zofia.b',
  [
    comparison('PADEL'),
    comparison('SQUASH', { your_level: 2.3, their_level: 2.55, percent_even: 51, level_gap: 0.25 }),
  ],
  'FRIEND',
);
/** Kuba — a stranger, evenest in tennis (81%), padel second: *0,09 above you*, **+**. */
const KUBA = player(2, 'kuba.w', [
  comparison('TENNIS', {
    your_level: 2.05,
    their_level: 2.14,
    percent_even: 81,
    level_gap: 0.09,
    your_band: { name: 'Developing', lower: 1.55, upper: 2.65 },
  }),
  comparison('PADEL', { their_level: 3.2, percent_even: 60, level_gap: 0.49 }),
]);
/** Ania — the reader asked: amber 62%, *Same level*, one sport. */
const ANIA = player(
  3,
  'ania.k',
  [comparison('PADEL', { their_level: 2.71, percent_even: 62, level_gap: 0 })],
  'SENT',
);
/** Michał — asked the reader: red 54%, one sport. */
const MICHAL = player(
  4,
  'michal.r',
  [comparison('PADEL', { their_level: 2.44, percent_even: 54, level_gap: -0.27 })],
  'ASKED_YOU',
);

const ROW = [ZOFIA, KUBA, ANIA, MICHAL];

/** One Hottest group and one Joiner, so the row has a neighbour either side. */
const HOT_GROUP: Wire['HottestGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000991',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  join_policy: 'ANYONE',
  run_by: 'tomek.k',
  club: { id: 'c0000000-0000-4000-8000-000000000991', name: 'Kazimierz Padel' },
  games_this_week: 2,
  new_this_month: 1,
  heat_share: 1,
  tag: 'HOTTEST',
  faces: [],
  friends_count: 0,
  relation: 'NONE',
  is_administrator: false,
};
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
 * **The Same level routes, faked** — the row and See all read each person's relation as the writes
 * left it; See all pages by `after`, and **a sport re-compares everybody holding a level in it** there.
 */
function levelServer(
  initially: readonly Wire['SameLevelPlayerSchema'][] = ROW,
  { pageSize = 20 }: { readonly pageSize?: number } = {},
) {
  let people = [...initially];
  const relationOf = (id: string) => people.find((one) => one.player_id === id)?.relation;

  stubGate(transport, { hasPlayerProfile: true });
  // The reader's own face, on the left of every card.
  stubOwnRecord(transport);
  transport.on('GET', SAME_LEVEL_PATH, () =>
    json<Wire['SameLevelResponse']>({ players: [...people], total: people.length }),
  );
  transport.on('GET', SAME_LEVEL_ALL_PATH, (request) => {
    const query = new URLSearchParams(request.path.split('?')[1] ?? '');
    const sport = query.get('sport');
    const kept =
      sport === null
        ? people
        : people.flatMap((one) => {
            const there = one.sports.find((each) => each.sport === sport);
            return there === undefined ? [] : [{ ...one, shown: there }];
          });
    const from = Number(query.get('after') ?? '0');
    return json<Wire['SameLevelPageResponse']>({
      players: kept.slice(from, from + pageSize),
      next: from + pageSize < kept.length ? String(from + pageSize) : null,
      sports: (['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'] as const).filter((each) =>
        people.some((one) => one.sports.some((held) => held.sport === each)),
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
        can_add_friend: true,
        nickname: one.nickname,
        photos: [],
        area_code: 'A+050612+0019938',
        social_tags: [],
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

const card = (person: Wire['SameLevelPlayerSchema']) =>
  within(screen.getByTestId(`same-level-${person.player_id}`));
const round = (person: Wire['SameLevelPlayerSchema'], relation: Wire['FriendRelation']) =>
  screen.findByRole('button', { name: roundLabel(relation, person.nickname) });
const rowReads = () => transport.requestsTo('GET', SAME_LEVEL_PATH).length;
const pageReads = () => transport.requestsTo('GET', SAME_LEVEL_ALL_PATH);
const asked = () => transport.requestsTo('POST', REQUESTS_PATH).map((request) => request.body);
const sheet = () => within(screen.getByTestId('bottom-sheet'));
const colourOf = (node: { readonly props: { readonly style?: unknown } }) =>
  (StyleSheet.flatten(node.props.style as TextStyle) ?? {}).color;

async function homeWithTheRow() {
  await launchSignedIn();
  await openLine(COPY.line);
}

describe('the line on Home', () => {
  it('stands second of the five — after Groups heating up, before New in Raketa — closed', async () => {
    levelServer();
    stubHottestGroups(transport, [HOT_GROUP]);
    stubNewInRaketa(transport, [JOINER]);
    await launchSignedIn();
    await screen.findByRole('button', { name: DISCOVERY_COPY.newInRaketa.line });
    await screen.findByRole('button', { name: GROUPS_COPY.hottest.line });

    expect(lineTitles().slice(0, 3)).toEqual([
      GROUPS_COPY.hottest.line,
      COPY.line,
      DISCOVERY_COPY.newInRaketa.line,
    ]);
    expect(isOpen(COPY.line)).toBe(false);
    expect(screen.queryAllByTestId(/^same-level-e0/)).toEqual([]);
  });

  /** ADR-0205 §5: *See all ›* at the bottom right of the open content, to the See all screen. */
  it('opens onto the cards in the read’s order, See all named at its foot', async () => {
    levelServer();
    await homeWithTheRow();

    const ids = screen
      .getAllByTestId(/^same-level-e0/)
      .map((node) => (node.props.testID as string).replace('same-level-', ''));
    expect(ids).toEqual(ROW.map((one) => one.player_id));
    expect(
      within(screen.getByTestId('same-level')).getByRole('link', { name: COPY.seeAllLabel }),
    ).toBeTruthy();
  });

  it('is hidden while the read holds nobody — no level anywhere', async () => {
    levelServer([]);
    await launchSignedIn();

    await waitFor(() => expect(rowReads()).toBeGreaterThan(0));
    await screen.findByText(/^Your games/);
    expect(screen.queryByRole('button', { name: COPY.line })).toBeNull();
  });

  it('is left out when its read fails, and the rest of Home stands', async () => {
    levelServer();
    transport.on('GET', SAME_LEVEL_PATH, () => errorResponse(503, 'block_state_unavailable'));
    await launchSignedIn();

    await waitFor(() => expect(rowReads()).toBeGreaterThan(0));
    expect(await screen.findByText(/^Your games/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: COPY.line })).toBeNull();
  });
});

describe('a card', () => {
  it('draws You and them, both levels, the % EVEN and the card’s sport', async () => {
    levelServer();
    await homeWithTheRow();

    const zofia = card(ZOFIA);
    expect(zofia.getByText(COPY.you)).toBeTruthy();
    expect(zofia.getByText('2,71')).toBeTruthy();
    expect(zofia.getByText('zofia.b')).toBeTruthy();
    expect(zofia.getByText('2,69')).toBeTruthy();
    expect(zofia.getByText('91%')).toBeTruthy();
    expect(zofia.getByText(COPY.even)).toBeTruthy();
    expect(zofia.getByText('Padel')).toBeTruthy();
    // Kuba's card shows the sport they are evenest in, with its levels.
    expect(card(KUBA).getByText('Tennis')).toBeTruthy();
    expect(card(KUBA).getByText('2,14')).toBeTruthy();
  });

  it('colours the % as the game cards do — green from 70, amber 55–69, red under 55', async () => {
    levelServer();
    await homeWithTheRow();

    expect(colourOf(card(ZOFIA).getByText('91%'))).toBe(theme.color.gameGreen);
    expect(colourOf(card(ANIA).getByText('62%'))).toBe(theme.color.gameAmber);
    expect(colourOf(card(MICHAL).getByText('54%'))).toBe(theme.color.gameRed);
  });

  it('says the gap in words — below, above, or the same level', async () => {
    levelServer();
    await homeWithTheRow();

    expect(card(ZOFIA).getByText('0,02 below you')).toBeTruthy();
    expect(card(KUBA).getByText('0,09 above you')).toBeTruthy();
    expect(card(ANIA).getByText(COPY.sameLevel)).toBeTruthy();
  });

  it('offers N sports › only with more than one shared sport', async () => {
    levelServer();
    await homeWithTheRow();

    expect(card(ZOFIA).getByText('2 sports')).toBeTruthy();
    expect(card(ANIA).queryByText(/sports$/)).toBeNull();
    expect(card(MICHAL).queryByText(/sports$/)).toBeNull();
  });

  it('draws the bar with the reader’s band named, and the YOU mark', async () => {
    levelServer();
    await homeWithTheRow();

    const bar = card(KUBA).getByTestId('comparison-bar', { includeHiddenElements: true });
    expect(within(bar).getByText('YOU', { includeHiddenElements: true })).toBeTruthy();
    expect(within(bar).getByText('Developing', { includeHiddenElements: true })).toBeTruthy();
  });

  it('opens the record from the face, and a request asked there was found at the card’s sport', async () => {
    levelServer();
    await homeWithTheRow();

    fireEvent.press(card(KUBA).getByRole('button', { name: 'kuba.w' }));
    fireEvent.press(await sheet().findByRole('button', { name: FRIENDS_COPY.record.add }));

    await waitFor(() =>
      expect(asked()).toEqual([
        { player_id: KUBA.player_id, made_from: 'SAME_LEVEL', sport: 'TENNIS' },
      ]),
    );
  });

  it('asks from the row with the card’s sport, and the card reads the answer where it stands', async () => {
    levelServer();
    await homeWithTheRow();
    const before = rowReads();

    fireEvent.press(await round(KUBA, 'NONE'));

    await waitFor(() =>
      expect(asked()).toEqual([
        { player_id: KUBA.player_id, made_from: 'SAME_LEVEL', sport: 'TENNIS' },
      ]),
    );
    expect(await round(KUBA, 'SENT')).toBeTruthy();
    // The row holds still under the thumb, read again on the next read (§9.1, §13).
    await waitFor(() => expect(queryClient.isMutating() + queryClient.isFetching()).toBe(0));
    expect(rowReads()).toBe(before);
  });
});

describe('the comparison sheet', () => {
  it('opens on N sports ›: You vs them, the worded button, a block per shared sport, most even first', async () => {
    levelServer();
    await homeWithTheRow();

    fireEvent.press(card(ZOFIA).getByRole('button', { name: /^Compare/ }));

    const shown = sheet();
    expect(shown.getByText('You vs zofia.b')).toBeTruthy();
    expect(shown.getByRole('button', { name: roundLabel('FRIEND', 'zofia.b') })).toBeTruthy();
    expect(shown.getByText(FRIENDS_COPY.round.worded.FRIEND)).toBeTruthy();
    const blocks = shown
      .getAllByTestId(/^comparison-/)
      .filter((node) =>
        /^comparison-(padel|tennis|squash|badminton)$/.test(node.props.testID as string),
      );
    expect(blocks.map((node) => node.props.testID as string)).toEqual([
      'comparison-padel',
      'comparison-squash',
    ]);
    const padel = within(blocks[0]!);
    expect(padel.getByText('Padel')).toBeTruthy();
    expect(padel.getByText('You 2,71 · zofia.b 2,69')).toBeTruthy();
    expect(padel.getByText('0,02 below you')).toBeTruthy();
    expect(padel.getByText('91% even')).toBeTruthy();
    const squash = within(blocks[1]!);
    expect(squash.getByText('You 2,30 · zofia.b 2,55')).toBeTruthy();
    expect(squash.getByText('0,25 above you')).toBeTruthy();
    expect(squash.getByText('51% even')).toBeTruthy();
  });

  it('tags each % in the light version of its colour', async () => {
    levelServer();
    await homeWithTheRow();

    fireEvent.press(card(ZOFIA).getByRole('button', { name: /^Compare/ }));

    expect(colourOf(sheet().getByText('91% even'))).toBe(theme.color.mintInk);
    expect(colourOf(sheet().getByText('51% even'))).toBe(theme.color.red);
  });

  it('its worded button asks from the row with the card’s sport', async () => {
    levelServer();
    await homeWithTheRow();

    fireEvent.press(card(KUBA).getByRole('button', { name: /^Compare/ }));
    fireEvent.press(sheet().getByRole('button', { name: roundLabel('NONE', 'kuba.w') }));

    await waitFor(() =>
      expect(asked()).toEqual([
        { player_id: KUBA.player_id, made_from: 'SAME_LEVEL', sport: 'TENNIS' },
      ]),
    );
    expect(await sheet().findByRole('button', { name: roundLabel('SENT', 'kuba.w') })).toBeTruthy();
  });
});

describe('the comparison sheet, when its person leaves the row', () => {
  it('stays up through the ask, closes once a read moves them out, and never reopens by itself', async () => {
    levelServer();
    await homeWithTheRow();
    // Asking Kuba makes him a gap, and a fresh match behind him takes his place among the ten.
    transport.on('POST', REQUESTS_PATH, () => {
      transport.on('GET', SAME_LEVEL_PATH, () =>
        json<Wire['SameLevelResponse']>({ players: [ZOFIA, ANIA, MICHAL], total: 3 }),
      );
      return json<Wire['RelationResponse']>({ relation: 'SENT' });
    });

    fireEvent.press(card(KUBA).getByRole('button', { name: /^Compare/ }));
    fireEvent.press(sheet().getByRole('button', { name: roundLabel('NONE', 'kuba.w') }));

    // The row holds still under the sheet, which reads the answer …
    expect(await sheet().findByRole('button', { name: roundLabel('SENT', 'kuba.w') })).toBeTruthy();
    expect(screen.getByTestId(`same-level-${KUBA.player_id}`)).toBeTruthy();

    // … until the next read — the app foregrounded with it up — moves him off the ten.
    await act(() => queryClient.invalidateQueries({ queryKey: ['discovery'] }));
    await waitFor(() => expect(screen.queryByTestId(`same-level-${KUBA.player_id}`)).toBeNull());
    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());

    // A later read brings him back, as a gap: his sheet stays shut until it is tapped.
    transport.on('GET', SAME_LEVEL_PATH, () =>
      json<Wire['SameLevelResponse']>({
        players: [ZOFIA, { ...KUBA, relation: 'SENT' }],
        total: 2,
      }),
    );
    await act(() => queryClient.invalidateQueries({ queryKey: ['discovery'] }));
    expect(await round(KUBA, 'SENT')).toBeTruthy();
    expect(screen.queryByTestId('bottom-sheet')).toBeNull();
  });
});

// The request waits in Needs your answer since #816, and its tile says no found-by line (ADR-0205 §1):
// where it was found is still served, and drawn nowhere.
describe('a request from Same competitive level, in Needs your answer', () => {
  const request = (
    over: Partial<Wire['HomeFriendRequestSchema']>,
  ): Wire['HomeFriendRequestSchema'] => ({
    player_id: MICHAL.player_id,
    nickname: MICHAL.nickname,
    photo_id: null,
    photo_url: null,
    asked_at: '2026-11-13T07:00:00Z',
    by_link: false,
    from_ranking: false,
    from_new_players: false,
    from_same_level: true,
    from_same_vibe: false,
    group: null,
    sport: 'PADEL',
    level: 2.44,
    player_score: 100,
    reliability_band: 'VERY_HIGH',
    percent_even: 91,
    in_common: null,
    levels: [],
    ...over,
  });

  it('says no line of where it was found, today’s % even included', async () => {
    levelServer();
    stubHome(transport, { friend_requests: [request({})] });
    await homeWithTheRow();
    await openNeedsYourAnswer();

    expect(screen.getByTestId(`friend-request-${MICHAL.player_id}`)).toBeTruthy();
    expect(screen.queryByText(/Your level in padel/)).toBeNull();
    expect(screen.queryByText(/Found you at your padel level/)).toBeNull();
  });
});

describe('See all', () => {
  async function openSeeAll() {
    await homeWithTheRow();
    fireEvent.press(screen.getByRole('link', { name: COPY.seeAllLabel }));
    await waitFor(() => expect(screen).toHavePathname('/same-level'));
    await screen.findByTestId('same-level-list');
  }
  const listed = () =>
    within(screen.getByTestId('same-level-list'))
      .getAllByTestId(/^same-level-e0/)
      .map((node) => (node.props.testID as string).replace('same-level-', ''));

  it('is pushed over Home, the tab still lit, titled with the pill on All', async () => {
    levelServer();
    await openSeeAll();

    expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();
    expect(screen.getByText(COPY.title)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sport: All' })).toBeTruthy();
  });

  it('draws a full-width card for everybody, in the read’s order, each keeping N sports ›', async () => {
    levelServer();
    await openSeeAll();

    expect(listed()).toEqual(ROW.map((one) => one.player_id));
    const list = within(screen.getByTestId('same-level-list'));
    expect(list.getAllByText('2 sports')).toHaveLength(2);
  });

  it('offers All and the sports served; a sport re-reads with it and re-compares everybody there', async () => {
    levelServer();
    await openSeeAll();

    fireEvent.press(screen.getByRole('button', { name: 'Sport: All' }));
    const bar = within(screen.getByTestId('sport-bar'));
    expect(
      bar.getAllByRole('button').map((option) => option.props.accessibilityLabel as string),
    ).toEqual(['Padel', 'Tennis', 'Squash', 'All']);

    fireEvent.press(bar.getByRole('button', { name: 'Padel' }));
    await waitFor(() => expect(pageReads().at(-1)!.path).toContain('sport=PADEL'));
    // Kuba is compared in padel now: 60%, amber, 0,49 above.
    await waitFor(() => expect(card(KUBA).getByText('60%')).toBeTruthy());
    expect(card(KUBA).getByText('0,49 above you')).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Sport: Padel' }));
    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Squash' }),
    );
    await waitFor(() => expect(listed()).toEqual([ZOFIA.player_id]));
  });

  it('reads the next page as the list nears its end, and never twice', async () => {
    const many = Array.from({ length: 6 }, (_, at) =>
      player(20 + at, `level.${at}`, [comparison('PADEL', { percent_even: 90 - at })]),
    );
    levelServer(many, { pageSize: 4 });
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

  it('says so when a sport leaves nobody to compare', async () => {
    levelServer();
    await openSeeAll();
    transport.on('GET', SAME_LEVEL_ALL_PATH, () =>
      json<Wire['SameLevelPageResponse']>({ players: [], next: null, sports: ['PADEL'] }),
    );

    fireEvent.press(screen.getByRole('button', { name: 'Sport: All' }));
    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Squash' }),
    );

    expect(await screen.findByText(nobodyToCompareIn('squash'))).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sport: Squash' })).toBeTruthy();
  });
});
