/**
 * **NEW IN RAKETA on Home, its See all, and the round friend button** — walked through the real route
 * tree ([#801](https://github.com/Raketa02/Raketa/issues/801), PRD #789; ADR-0204 §5; the Home rows
 * screens §5, §8; the mechanics §7, §11–§13; the words §31.7, §31.9, §31.10).
 *
 * - **The row**: after Hottest groups, *See all ›* named; gone while empty or failed; the tiles' faces,
 *   *NEW*, sports with their levels — none without a level — and the Joined ladder.
 * - **The round button**: every state's mark and name; **+** asks at once and draws **…** before the
 *   answer; **…** opens *Request sent* · *Cancel request*; **✓** asks *Remove … as a friend?*; the
 *   envelope accepts at once. A failed write puts it back.
 * - **One tap, everywhere**: a write re-reads every Discovery read, Home's answer on a request card
 *   re-reads the row, and a request from the record a tile opens says *new players*.
 * - **See all**: pushed over Home with the tab lit, the pill, a sport's filter, paging and the empty line.
 * - **The request card** on the receiver's Home reads *Found you among new players*.
 *
 * **The routes are answered by a small fake of the server** (`peopleServer`): a write moves the
 * person's relation, and the row and See all read it back — so what a tile draws after a write is the
 * read again, never this client guessing, beyond what the button draws while the write is out.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { FlatList } from 'react-native';

import { FRIENDS_COPY, removeTitle, roundLabel } from '@/features/friends/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { GROUPS_COPY } from '@/features/groups/types';
import {
  HOME_PATH,
  HOTTEST_GROUPS_PATH,
  NEW_IN_RAKETA_ALL_PATH,
  NEW_IN_RAKETA_PATH,
  launchSignedIn,
  stubGate,
  stubHome,
  stubHottestGroups,
} from '@/test-support/onboardingRouter';
import { servedReliability } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { DISCOVERY_COPY, nobodyNewPlays } from './discoveryCopy';

const COPY = DISCOVERY_COPY.newInRaketa;
const HIDDEN = { includeHiddenElements: true } as const;

const joiner = (
  n: number,
  nickname: string,
  over: Partial<Wire['NewInRaketaPlayerSchema']> = {},
): Wire['NewInRaketaPlayerSchema'] => ({
  player_id: `e0000000-0000-4000-8000-0000000008${String(n).padStart(2, '0')}`,
  nickname,
  photo_id: null,
  photo_url: null,
  joined_at: '2026-11-12T10:00:00Z',
  days_since_joined: 2,
  sports: [],
  relation: 'NONE',
  ...over,
});

/** Bartek — 2 days, padel and badminton, a stranger: **+**. */
const BARTEK = joiner(1, 'bartek.l', {
  sports: [
    { sport: 'PADEL', level: 2.35 },
    { sport: 'BADMINTON', level: 2.1 },
  ],
});
/** Ola — joined yesterday, no level yet: no sport lines. */
const OLA = joiner(2, 'ola.n', { days_since_joined: 1 });
/** Michał — asked the reader: the envelope. */
const MICHAL = joiner(3, 'michal.r', {
  days_since_joined: 3,
  relation: 'ASKED_YOU',
  sports: [
    { sport: 'PADEL', level: 2.44 },
    { sport: 'TENNIS', level: 2.6 },
  ],
});
/** Piotr — the reader asked: **…**. */
const PIOTR = joiner(4, 'piotr.s', {
  days_since_joined: 9,
  relation: 'SENT',
  sports: [{ sport: 'SQUASH', level: 2.61 }],
});
/** Filip — a friend: **✓**. */
const FILIP = joiner(5, 'filip.n', {
  days_since_joined: 16,
  relation: 'FRIEND',
  sports: [{ sport: 'PADEL', level: 2.6 }],
});

const ROW = [BARTEK, OLA, MICHAL, PIOTR, FILIP];

/** One Hottest group, so the row has a neighbour to stand after. */
const HOT_GROUP: Wire['HottestGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000881',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  join_policy: 'ANYONE',
  run_by: 'tomek.k',
  club: { id: 'c0000000-0000-4000-8000-000000000881', name: 'Kazimierz Padel' },
  games_this_week: 2,
  new_this_month: 1,
  heat_share: 1,
  tag: 'HOTTEST',
  faces: [],
  friends_count: 0,
  relation: 'NONE',
  is_administrator: false,
};

const REQUESTS_PATH = '/api/v1/friends/requests';
const requestPath = (id: string) => `${REQUESTS_PATH}/${id}`;
const friendPath = (id: string) => `/api/v1/friends/${id}`;
const recordPath = (id: string) => `/api/v1/players/${id}/record`;

let transport: Transport;

/**
 * **The people routes, faked** — the row and See all read each person's relation as the writes left
 * it; See all pages by `after` and filters by `sport`. `refuseNextAsk` fails the next request with a
 * code; `holdAsks` makes asks wait for the returned release.
 */
function peopleServer(
  initially: readonly Wire['NewInRaketaPlayerSchema'][] = ROW,
  { pageSize = 20 }: { readonly pageSize?: number } = {},
) {
  let people = [...initially];
  let refusal: { status: number; code: string } | undefined;
  let held: Promise<void> | undefined;
  const move = (id: string, relation: Wire['FriendRelation']) => {
    people = people.map((one) => (one.player_id === id ? { ...one, relation } : one));
  };
  const relationOf = (id: string) => people.find((one) => one.player_id === id)?.relation;

  stubGate(transport, { hasPlayerProfile: true });
  transport.on('GET', NEW_IN_RAKETA_PATH, () =>
    json<Wire['NewInRaketaResponse']>({ players: [...people] }),
  );
  transport.on('GET', NEW_IN_RAKETA_ALL_PATH, (request) => {
    const query = new URLSearchParams(request.path.split('?')[1] ?? '');
    const sport = query.get('sport');
    const kept =
      sport === null ? people : people.filter((one) => one.sports.some((s) => s.sport === sport));
    const from = Number(query.get('after') ?? '0');
    const page = kept.slice(from, from + pageSize);
    return json<Wire['NewInRaketaPageResponse']>({
      players: page,
      next: from + pageSize < kept.length ? String(from + pageSize) : null,
      sports: (['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'] as const).filter((each) =>
        people.some((one) => one.sports.some((s) => s.sport === each)),
      ),
    });
  });

  transport.on('POST', REQUESTS_PATH, async (request) => {
    if (held !== undefined) await held;
    const { player_id: id } = request.body as Wire['AskToBeFriendsRequest'];
    if (refusal !== undefined) {
      const { status, code } = refusal;
      refusal = undefined;
      if (code === 'player_unavailable') people = people.filter((one) => one.player_id !== id);
      return errorResponse(status, code);
    }
    const relation = relationOf(id) === 'ASKED_YOU' ? 'FRIEND' : 'SENT';
    move(id, relation);
    return json<Wire['RelationResponse']>({ relation });
  });
  for (const one of initially) {
    transport.on('POST', `${requestPath(one.player_id)}/acceptance`, async () => {
      if (held !== undefined) await held;
      move(one.player_id, 'FRIEND');
      return json<Wire['RelationResponse']>({ relation: 'FRIEND' });
    });
    transport.on('DELETE', requestPath(one.player_id), () => {
      move(one.player_id, 'NONE');
      return noContent();
    });
    transport.on('DELETE', friendPath(one.player_id), () => {
      move(one.player_id, 'NONE');
      return noContent();
    });
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

  return {
    refuseNextAsk: (status: number, code: string) => {
      refusal = { status, code };
    },
    holdAsks: () => {
      let release: () => void = () => {};
      held = new Promise<void>((resolve) => {
        release = resolve;
      });
      return release;
    },
  };
}

beforeEach(() => {
  transport = installTransport();
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  jest.useRealTimers();
  transport.restore();
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
  resetSessionStatus();
  await clearStoredTokens();
});

const tile = (person: Wire['NewInRaketaPlayerSchema']) =>
  within(screen.getByTestId(`joiner-${person.player_id}`));
const round = (person: Wire['NewInRaketaPlayerSchema'], relation: Wire['FriendRelation']) =>
  screen.findByRole('button', { name: roundLabel(relation, person.nickname) });
const rowReads = () => transport.requestsTo('GET', NEW_IN_RAKETA_PATH).length;
const asked = () => transport.requestsTo('POST', REQUESTS_PATH).map((request) => request.body);
const sheet = () => within(screen.getByTestId('bottom-sheet'));
/** See all's own pull — Home's stays mounted under it, with its own. */
const pullSeeAll = () =>
  screen.UNSAFE_getByType(FlatList).props.refreshControl.props.onRefresh() as Promise<void>;
const toasts = () => useToastQueue.getState().queue.map((toast) => toast.message);

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

describe('the row on Home', () => {
  it('stands right after Hottest groups, with See all named for what it opens', async () => {
    peopleServer();
    stubHottestGroups(transport, [HOT_GROUP]);
    await homeWithTheRow();
    await screen.findByRole('header', { name: GROUPS_COPY.hottest.heading });

    const order = headings();
    const games = order.findIndex((text) => text.startsWith('Your games'));
    expect(order.slice(games + 1, games + 3)).toEqual([GROUPS_COPY.hottest.heading, COPY.heading]);
    expect(
      within(screen.getByTestId('new-in-raketa')).getByRole('link', { name: COPY.seeAllLabel }),
    ).toBeTruthy();
  });

  it('draws the tiles in the read’s order', async () => {
    peopleServer();
    await homeWithTheRow();

    const ids = screen
      .getAllByTestId(/^joiner-e0/)
      .map((node) => (node.props.testID as string).replace('joiner-', ''));
    expect(ids).toEqual(ROW.map((one) => one.player_id));
  });

  it('is gone with its heading while the read holds nobody', async () => {
    peopleServer([]);
    await launchSignedIn();

    await waitFor(() => expect(rowReads()).toBeGreaterThan(0));
    await screen.findByText(/^Your games/);
    expect(screen.queryByRole('header', { name: COPY.heading })).toBeNull();
  });

  it('is left out when its read fails, and the rest of Home stands', async () => {
    peopleServer();
    transport.on('GET', NEW_IN_RAKETA_PATH, () => errorResponse(503, 'block_state_unavailable'));
    await launchSignedIn();

    await waitFor(() => expect(rowReads()).toBeGreaterThan(0));
    expect(await screen.findByText(/^Your games/)).toBeTruthy();
    expect(screen.queryByRole('header', { name: COPY.heading })).toBeNull();
  });
});

describe('a tile', () => {
  it('draws NEW, the nickname, every sport with its level, and when they joined', async () => {
    peopleServer();
    await homeWithTheRow();

    const bartek = tile(BARTEK);
    expect(bartek.getByText(COPY.tag)).toBeTruthy();
    expect(bartek.getByText('bartek.l')).toBeTruthy();
    expect(bartek.getByText('Padel 2,35')).toBeTruthy();
    expect(bartek.getByText('Badminton 2,10')).toBeTruthy();
    expect(bartek.getByText('Joined 2 days ago')).toBeTruthy();
    expect(
      screen.getByRole('button', {
        name: 'bartek.l, Padel 2,35, Badminton 2,10, Joined 2 days ago',
      }),
    ).toBeTruthy();
  });

  it('draws no sport line for a player with no level', async () => {
    peopleServer();
    await homeWithTheRow();

    const ola = tile(OLA);
    expect(ola.getByText('ola.n')).toBeTruthy();
    expect(ola.queryByTestId(/^joiner-sport-/)).toBeNull();
    expect(ola.getByText('Joined yesterday')).toBeTruthy();
  });

  it('says when each joined by the ladder, with no weekday', async () => {
    peopleServer([
      joiner(11, 'today.a', { days_since_joined: 0 }),
      joiner(12, 'week.b', { days_since_joined: 9 }),
      joiner(13, 'weeks.c', { days_since_joined: 16 }),
      joiner(14, 'month.d', { days_since_joined: 29 }),
    ]);
    await homeWithTheRow();

    for (const line of [
      'Joined today',
      'Joined last week',
      'Joined 2 weeks ago',
      'Joined 4 weeks ago',
    ]) {
      expect(screen.getByText(line)).toBeTruthy();
    }
  });

  it('opens the record, and a request asked there was found among new players', async () => {
    peopleServer();
    await homeWithTheRow();

    fireEvent.press(
      screen.getByRole('button', {
        name: 'bartek.l, Padel 2,35, Badminton 2,10, Joined 2 days ago',
      }),
    );
    const add = await sheet().findByRole('button', { name: FRIENDS_COPY.record.add });
    const before = rowReads();
    fireEvent.press(add);

    await waitFor(() =>
      expect(asked()).toEqual([{ player_id: BARTEK.player_id, made_from: 'NEW_PLAYERS' }]),
    );
    // The row under the record moves with it.
    await waitFor(() => expect(rowReads()).toBeGreaterThan(before));
    expect(await round(BARTEK, 'SENT')).toBeTruthy();
  });
});

describe('the round friend button', () => {
  it('draws each relation’s mark, named for whom', async () => {
    peopleServer();
    await homeWithTheRow();

    expect(await round(BARTEK, 'NONE')).toBeTruthy();
    expect(await round(PIOTR, 'SENT')).toBeTruthy();
    expect(await round(FILIP, 'FRIEND')).toBeTruthy();
    expect(await round(MICHAL, 'ASKED_YOU')).toBeTruthy();
    expect(screen.getByRole('button', { name: "Accept michal.r's request" })).toBeTruthy();
    expect(tile(MICHAL).getByTestId('round-friend-halo', HIDDEN)).toBeTruthy();
    expect(tile(BARTEK).queryByTestId('round-friend-halo', HIDDEN)).toBeNull();
  });

  it('+ asks from new players at once, drawing … before the answer lands', async () => {
    const server = peopleServer();
    await homeWithTheRow();
    const release = server.holdAsks();

    fireEvent.press(await round(BARTEK, 'NONE'));

    // Out, and already drawn as sent.
    expect(await round(BARTEK, 'SENT')).toBeTruthy();
    await act(async () => release());
    await waitFor(() =>
      expect(asked()).toEqual([{ player_id: BARTEK.player_id, made_from: 'NEW_PLAYERS' }]),
    );
    expect(await round(BARTEK, 'SENT')).toBeTruthy();
  });

  it('… opens Request sent, and Cancel request takes it back to +', async () => {
    peopleServer();
    await homeWithTheRow();

    fireEvent.press(await round(PIOTR, 'SENT'));
    expect(sheet().getByText(FRIENDS_COPY.round.requestSent.title)).toBeTruthy();
    expect(sheet().queryByRole('button', { name: FRIENDS_COPY.record.keep })).toBeNull();
    fireEvent.press(sheet().getByRole('button', { name: FRIENDS_COPY.round.requestSent.act }));

    expect(await round(PIOTR, 'NONE')).toBeTruthy();
    expect(transport.requestsTo('DELETE', requestPath(PIOTR.player_id))).toHaveLength(1);
  });

  it('✓ asks first: Keep writes nothing, Remove friend takes it back to +', async () => {
    peopleServer();
    await homeWithTheRow();

    fireEvent.press(await round(FILIP, 'FRIEND'));
    expect(sheet().getByText(removeTitle('filip.n'))).toBeTruthy();
    fireEvent.press(sheet().getByRole('button', { name: FRIENDS_COPY.record.keep }));
    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());
    expect(transport.requestsTo('DELETE', friendPath(FILIP.player_id))).toHaveLength(0);

    fireEvent.press(await round(FILIP, 'FRIEND'));
    fireEvent.press(sheet().getByRole('button', { name: FRIENDS_COPY.record.remove.act }));

    expect(await round(FILIP, 'NONE')).toBeTruthy();
    expect(transport.requestsTo('DELETE', friendPath(FILIP.player_id))).toHaveLength(1);
  });

  it('the envelope accepts at once, drawing ✓, and Home is read again', async () => {
    const server = peopleServer();
    await homeWithTheRow();
    const homeReads = transport.requestsTo('GET', HOME_PATH).length;
    const release = server.holdAsks();

    fireEvent.press(await round(MICHAL, 'ASKED_YOU'));

    expect(await round(MICHAL, 'FRIEND')).toBeTruthy();
    await act(async () => release());
    await waitFor(() =>
      expect(
        transport.requestsTo('POST', `${requestPath(MICHAL.player_id)}/acceptance`),
      ).toHaveLength(1),
    );
    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeReads),
    );
    expect(await round(MICHAL, 'FRIEND')).toBeTruthy();
  });

  it('a refused ask puts + back and says why', async () => {
    const server = peopleServer();
    await homeWithTheRow();
    server.refuseNextAsk(409, 'unblock_them_first');

    fireEvent.press(await round(BARTEK, 'NONE'));

    expect(await round(BARTEK, 'NONE')).toBeTruthy();
    await waitFor(() => expect(toasts()).toEqual([FRIENDS_COPY.refused.unblock_them_first]));
  });

  it('an ask refused because they turned Show me to new people off says nothing, and the tile leaves', async () => {
    const server = peopleServer();
    await homeWithTheRow();
    server.refuseNextAsk(404, 'player_unavailable');

    fireEvent.press(await round(BARTEK, 'NONE'));

    await waitFor(() => expect(screen.queryByTestId(`joiner-${BARTEK.player_id}`)).toBeNull());
    expect(toasts()).toEqual([]);
  });

  it('one tap re-reads the row, and Hottest groups, whose faces are friends first', async () => {
    peopleServer();
    await homeWithTheRow();
    const before = rowReads();
    const hottest = transport.requestsTo('GET', HOTTEST_GROUPS_PATH).length;

    fireEvent.press(await round(MICHAL, 'ASKED_YOU'));

    await waitFor(() => expect(rowReads()).toBeGreaterThan(before));
    await waitFor(() =>
      expect(transport.requestsTo('GET', HOTTEST_GROUPS_PATH).length).toBeGreaterThan(hottest),
    );
  });

  it('never reopens a sheet by itself once the read moved under it', async () => {
    peopleServer([PIOTR, BARTEK]);
    await homeWithTheRow();
    fireEvent.press(await round(PIOTR, 'SENT'));
    expect(sheet().getByText(FRIENDS_COPY.round.requestSent.title)).toBeTruthy();

    // Piotr's request is answered elsewhere: the read says nothing stands between them now…
    transport.on('GET', NEW_IN_RAKETA_PATH, () =>
      json<Wire['NewInRaketaResponse']>({ players: [{ ...PIOTR, relation: 'NONE' }, BARTEK] }),
    );
    await act(() => queryClient.invalidateQueries({ queryKey: ['discovery'] }));
    expect(await round(PIOTR, 'NONE')).toBeTruthy();
    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());

    // …and once it says sent again, the sheet stays shut until it is tapped.
    transport.on('GET', NEW_IN_RAKETA_PATH, () =>
      json<Wire['NewInRaketaResponse']>({ players: [PIOTR, BARTEK] }),
    );
    await act(() => queryClient.invalidateQueries({ queryKey: ['discovery'] }));
    expect(await round(PIOTR, 'SENT')).toBeTruthy();
    expect(screen.queryByTestId('bottom-sheet')).toBeNull();
  });
});

describe('Home’s request card', () => {
  it('reads Found you among new players, and accepting it turns the envelope to ✓', async () => {
    peopleServer();
    stubHome(transport, {
      friend_requests: [
        {
          player_id: MICHAL.player_id,
          nickname: MICHAL.nickname,
          photo_id: null,
          photo_url: null,
          asked_at: '2026-11-13T07:00:00Z',
          by_link: false,
          from_ranking: false,
          from_new_players: true,
          group: null,
          sport: null,
          level: null,
          player_score: 100,
          reliability_band: 'VERY_HIGH',
        },
      ],
    });
    await homeWithTheRow();

    expect(await screen.findByText(FRIENDS_COPY.home.newPlayers, { exact: false })).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: `Accept ${MICHAL.nickname}` }));

    expect(await round(MICHAL, 'FRIEND')).toBeTruthy();
  });
});

describe('See all', () => {
  async function openSeeAll() {
    await homeWithTheRow();
    fireEvent.press(screen.getByRole('link', { name: COPY.seeAllLabel }));
    await waitFor(() => expect(screen).toHavePathname('/new-in-raketa'));
    await screen.findByTestId('new-in-raketa-grid');
  }

  it('is pushed over Home, the tab still lit, titled with the pill on All', async () => {
    peopleServer();
    await openSeeAll();

    expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();
    expect(screen.getByText(COPY.title)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sport: All' })).toBeTruthy();
  });

  it('draws the tiles in two columns, newest first', async () => {
    peopleServer();
    await openSeeAll();

    const grid = screen.getByTestId('new-in-raketa-grid');
    expect(screen.UNSAFE_getByType(FlatList).props.numColumns).toBe(2);
    expect(
      within(grid)
        .getAllByTestId(/^joiner-e0/)
        .map((node) => node.props.testID as string),
    ).toEqual(ROW.map((one) => `joiner-${one.player_id}`));
  });

  it('reads the next page as the grid nears its end, and never twice', async () => {
    const many = Array.from({ length: 6 }, (_, at) =>
      joiner(20 + at, `joiner.${at}`, { days_since_joined: at }),
    );
    peopleServer(many, { pageSize: 4 });
    await openSeeAll();
    const reads = () => transport.requestsTo('GET', NEW_IN_RAKETA_ALL_PATH);
    const drawn = () =>
      within(screen.getByTestId('new-in-raketa-grid')).getAllByTestId(/^joiner-e0/).length;
    expect(reads()).toHaveLength(1);
    expect(drawn()).toBe(4);

    fireEvent(screen.UNSAFE_getByType(FlatList), 'endReached');
    fireEvent(screen.UNSAFE_getByType(FlatList), 'endReached');

    await waitFor(() => expect(reads()).toHaveLength(2));
    expect(reads()[1]!.path).toContain('after=4');
    await waitFor(() => expect(drawn()).toBe(6));
    fireEvent(screen.UNSAFE_getByType(FlatList), 'endReached');
    expect(reads()).toHaveLength(2);
  });

  it('keeps the pill when a sport’s read fails, so All is a tap away', async () => {
    peopleServer();
    await openSeeAll();
    const served = transport.requestsTo('GET', NEW_IN_RAKETA_ALL_PATH).length;
    transport.on('GET', NEW_IN_RAKETA_ALL_PATH, () =>
      errorResponse(400, 'not_a_new_in_raketa_page'),
    );

    fireEvent.press(screen.getByRole('button', { name: 'Sport: All' }));
    fireEvent.press(within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Padel' }));

    await waitFor(() =>
      expect(transport.requestsTo('GET', NEW_IN_RAKETA_ALL_PATH).length).toBeGreaterThan(served),
    );
    expect(await screen.findByRole('alert')).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: 'Sport: Padel' }));
    expect(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'All' }),
    ).toBeTruthy();
  });

  it('offers the sports served, filters by one, and says when it leaves nobody', async () => {
    peopleServer();
    await openSeeAll();

    fireEvent.press(screen.getByRole('button', { name: 'Sport: All' }));
    const bar = within(screen.getByTestId('sport-bar'));
    expect(
      bar.getAllByRole('button').map((option) => option.props.accessibilityLabel as string),
    ).toEqual(['Padel', 'Tennis', 'Squash', 'Badminton', 'All']);

    fireEvent.press(bar.getByRole('button', { name: 'Squash' }));
    await waitFor(() =>
      expect(transport.requestsTo('GET', NEW_IN_RAKETA_ALL_PATH).at(-1)!.path).toContain(
        'sport=SQUASH',
      ),
    );
    await waitFor(() =>
      expect(
        within(screen.getByTestId('new-in-raketa-grid'))
          .getAllByTestId(/^joiner-e0/)
          .map((node) => node.props.testID as string),
      ).toEqual([`joiner-${PIOTR.player_id}`]),
    );

    // Piotr leaves before the sport is read again: nobody new plays squash.
    transport.on('GET', NEW_IN_RAKETA_ALL_PATH, () =>
      json<Wire['NewInRaketaPageResponse']>({ players: [], next: null, sports: ['PADEL'] }),
    );
    await act(async () => {
      await pullSeeAll();
    });
    expect(await screen.findByText(nobodyNewPlays('squash'))).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sport: Squash' })).toBeTruthy();
  });

  it('a tap on a grid tile’s button re-reads the grid and the row under it', async () => {
    peopleServer();
    await openSeeAll();
    const rows = rowReads();
    const grids = transport.requestsTo('GET', NEW_IN_RAKETA_ALL_PATH).length;

    fireEvent.press(await round(BARTEK, 'NONE'));

    await waitFor(() => expect(rowReads()).toBeGreaterThan(rows));
    await waitFor(() =>
      expect(transport.requestsTo('GET', NEW_IN_RAKETA_ALL_PATH).length).toBeGreaterThan(grids),
    );
    expect(await round(BARTEK, 'SENT')).toBeTruthy();
  });

  it('says the failure, and Try again reads it again', async () => {
    jest.useFakeTimers();
    peopleServer();
    transport.on('GET', NEW_IN_RAKETA_ALL_PATH, () => errorResponse(503, 'service_unavailable'));
    await homeWithTheRow();
    fireEvent.press(screen.getByRole('link', { name: COPY.seeAllLabel }));
    // Through the automatic retries the error model allows.
    await act(() => jest.advanceTimersByTimeAsync(30_000));

    const again = await screen.findByRole('button', { name: 'Try again' });
    expect(screen.getByRole('alert')).toBeTruthy();

    peopleServer();
    fireEvent.press(again);
    expect(await screen.findByTestId(`joiner-${BARTEK.player_id}`)).toBeTruthy();
  });
});
