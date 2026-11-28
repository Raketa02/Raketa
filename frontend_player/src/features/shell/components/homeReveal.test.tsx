/**
 * **Home shimmers until it is built, then reveals together** — walked through the real route tree
 * ([#871](https://github.com/Rakieta02/Rakieta/issues/871); PRD #867; the loading shimmer log §5, §6).
 *
 * Home's reads are held on their way by the fake server and landed when a walk says. What is asserted
 * is what a player sees: whether a skeleton is drawn (found by its id, since it is hidden from a
 * listener), which content's names are there, and the header's numbers. The rule's own table and the
 * ceiling's timer are `Reveal.test.tsx`'s; the shapes and the band, `Skeleton.test.tsx`'s.
 *
 * **What the harness does to time.** Its fake clock exists only once it has launched, and every
 * navigation runs every pending timer — the launch's own included, which comes as Home mounts. So:
 *
 * - **The ceiling has passed by the time a walk looks** (its timer is one of them): these walks are of
 *   the rule from the ceiling on — the finished parts from the top, never FOR YOU before your things,
 *   the header's numbers as they land. Before the ceiling — everything together, the numbers held
 *   with it — is the hook's, in `Reveal.test.tsx`, on a clock nothing else runs.
 * - **A held read is deaf to the client's abort** (`deafToAborts`): its 15 s timeout is one of those
 *   timers too, and a read timed out is one that failed once and is retrying — finished, by the
 *   rule. Deaf, it stays on its way until the walk answers it, as a slow server's would.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { RefreshControl } from 'react-native';

import { DISCOVERY_COPY } from '@/features/discovery/types';
import { GROUPS_COPY } from '@/features/groups/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { REVEAL_CEILING, theme } from '@/shared/ui';
import { lineTitles } from '@/test-support/forYou';
import { homeGame, stubHomeGames } from '@/test-support/home';
import { envelope } from '@/test-support/needsYourAnswer';
import {
  HOME_PATH,
  HOTTEST_GROUPS_PATH,
  MY_GROUPS_PATH,
  NEW_IN_RAKIETA_PATH,
  NOTICES_PATH,
  SAME_LEVEL_PATH,
  SAME_VIBE_PATH,
  TOP_TEN_PATH,
  launchSignedIn,
  stubGate,
  stubHottestGroups,
  stubMyGroups,
  stubNotices,
  stubSameLevel,
  stubTopTen,
} from '@/test-support/onboardingRouter';
import {
  deafToAborts,
  errorResponse,
  installTransport,
  json,
  servedBody,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { HOME_COPY } from './shellCopy';

const HIDDEN = { includeHiddenElements: true } as const;
/** Past Query's first retry's backoff (`queryClient.ts`'s `retryDelay`). */
const RETRY = 2_000;
const RATINGS_PATH = '/api/v1/ratings';

const GROUPS = GROUPS_COPY.hottest.line;
const LEVEL = DISCOVERY_COPY.sameLevel.line;
const TOP = 'Top 10';

const RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

const MINE: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000008719',
  kind: 'PLAYER',
  name: 'Podgórze',
  monogram: { letters: 'Po', colour: 2 },
  sports: ['PADEL'],
  member_count: 4,
  home_club: { id: 'c0000000-0000-4000-8000-000000008719', name: 'Podgórze Padel' },
};

const HOT_GROUP: Wire['HottestGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000008711',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  join_policy: 'ANYONE',
  run_by: 'tomek.k',
  club: { id: 'c0000000-0000-4000-8000-000000008711', name: 'Kazimierz Padel' },
  games_this_week: 2,
  new_this_month: 1,
  heat_share: 1,
  tag: 'HOTTEST',
  faces: [],
  friends_count: 0,
  relation: 'NONE',
  is_administrator: false,
};

const PADEL: Wire['SameLevelSportSchema'] = {
  sport: 'PADEL',
  your_level: 2.71,
  their_level: 2.69,
  percent_even: 91,
  level_gap: -0.02,
  your_band: { name: 'Established', lower: 2.65, upper: 3.85 },
};

const AT_YOUR_LEVEL: Wire['SameLevelPlayerSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000008712',
  nickname: 'zofia.b',
  photo_id: null,
  photo_url: null,
  shown: PADEL,
  sports: [PADEL],
  relation: 'NONE',
};

const RANKED: Wire['TopTenResponse'] = {
  sport: 'PADEL',
  anyone_listed: true,
  players: [
    {
      place: 1,
      player_id: 'e0000000-0000-4000-8000-000000008713',
      nickname: 'ines.d',
      photo_id: null,
      photo_url: null,
      level: 3.4,
      chip: null,
      is_you: false,
    },
  ],
};

/** Ana's friend request, waiting on the reader — what draws the envelope. */
const ASKED: Wire['HomeFriendRequestSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000008714',
  nickname: 'ana.k',
  photo_id: null,
  photo_url: null,
  asked_at: '2026-10-01T07:00:00Z',
  by_link: false,
  from_ranking: false,
  from_new_players: false,
  from_same_level: false,
  from_same_vibe: false,
  group: null,
  sport: 'PADEL',
  level: 3.4,
  player_score: 98,
  reliability_band: 'VERY_HIGH',
  percent_even: null,
  in_common: null,
  levels: [],
};

/** Every read Home waits on — your things', then FOR YOU's. */
const YOUR_THINGS = [HOME_PATH, RATINGS_PATH, MY_GROUPS_PATH, NOTICES_PATH] as const;
const FOR_YOU = [
  HOTTEST_GROUPS_PATH,
  SAME_LEVEL_PATH,
  NEW_IN_RAKIETA_PATH,
  SAME_VIBE_PATH,
  TOP_TEN_PATH,
] as const;
const EVERY_READ = [...YOUR_THINGS, ...FOR_YOU];

let transport: Transport;

/**
 * **Ana's Home, every read with something to show**: a booked game, a friend request waiting (the
 * envelope), three new notices (the bell's badge), 7th in padel (the trophy), and three of FOR YOU's
 * lines — Groups heating up, Players at your level and Top 10.
 */
function anasHome() {
  stubGate(transport, { hasPlayerProfile: true, ratings: [RATING] });
  stubMyGroups(transport, [MINE]);
  stubHomeGames(transport, [homeGame()], {
    friend_requests: [ASKED],
    needs_your_answer: { new_count: 1, watermark: ASKED.asked_at },
    ranking: { sport: 'PADEL', general_place: 7, friends_place: 4 },
  });
  stubNotices(transport, [], { newCount: 3 });
  stubHottestGroups(transport, [HOT_GROUP]);
  stubSameLevel(transport, [AT_YOUR_LEVEL]);
  stubTopTen(transport, RANKED);
}

interface Held {
  /** Answer every request held so far and from now on, as the server would. */
  readonly land: () => Promise<void>;
}

/**
 * **Holds every read of these routes on its way** until the walk lands them, deaf to the client's
 * timeout (see the module note) — every request, not the next one. Each is answered with what its
 * stub serves.
 */
function hold(paths: readonly string[]): Held {
  let release: () => void = () => {};
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  const answers = paths.map((path) => {
    const served = transport.answerNow('GET', path);
    if (!(served instanceof Response))
      throw new Error(`${path} is stubbed with no answer to hold.`);
    return [path, servedBody(served)] as const;
  });
  for (const [path, body] of answers) {
    transport.on(
      'GET',
      path,
      deafToAborts(() => held.then(() => json(body))),
    );
  }
  return {
    land: async () => {
      for (const [path, body] of answers) transport.on('GET', path, () => json(body));
      await act(async () => release());
      await settle();
    },
  };
}

/** Query's answers reach the screen on its next tick. */
async function settle() {
  await act(() => jest.advanceTimersByTimeAsync(0));
  await act(() => jest.advanceTimersByTimeAsync(0));
}

/** Launched onto Home, its reads set out — whatever is held is still out. */
async function onHome() {
  await launchSignedIn();
  await screen.findByTestId('home-parts', HIDDEN);
  await waitFor(() => expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(0));
  await settle();
}

const skeletonOf = (part: 'your-games' | 'for-you') =>
  screen.queryByTestId(`${part}-skeleton`, HIDDEN);
/** *Your games* and its count, as a player reads it — `null` until it is revealed. */
const yourGames = () => screen.queryByText(/^Your games/);
const forYouHeading = () => screen.queryByRole('header', { name: HOME_COPY.forYou });
const bell = () => screen.getByRole('button', { name: /^Recent notifications/ });
const trophy = () => screen.getByTestId('ranking-trophy');
const placeOnTrophy = () => screen.queryByText('#7');

/** Past the reveal's cross-fade, so a skeleton that is going has gone. */
function pastTheFade() {
  act(() => jest.advanceTimersByTime(theme.motion.fade + 16));
}

beforeEach(() => {
  transport = installTransport();
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  await forgetPhonePreferences();
});

describe('while Home’s reads are out', () => {
  it('shimmers: Your games’ heading and a card, FOR YOU’s heading and four lines — the header drawn for real', async () => {
    anasHome();
    hold(EVERY_READ);
    await onHome();

    expect(skeletonOf('your-games')).not.toBeNull();
    expect(skeletonOf('for-you')).not.toBeNull();
    expect(screen.getAllByTestId('your-games-skeleton-card', HIDDEN)).toHaveLength(1);
    expect(screen.getAllByTestId('for-you-skeleton-line', HIDDEN)).toHaveLength(4);
    expect(yourGames()).toBeNull();
    expect(forYouHeading()).toBeNull();
    // The header is real: its title, the bell and the trophy, each a button.
    expect(screen.getByRole('header', { name: HOME_COPY.title })).toBeTruthy();
    expect(bell()).toBeTruthy();
    expect(trophy()).toBeTruthy();
  });

  it('never says Your games · 0 before Home’s read lands, even underneath', async () => {
    anasHome();
    stubHomeGames(transport, []);
    const home = hold([HOME_PATH]);
    await onHome();

    expect(screen.queryByText('Your games · 0', HIDDEN)).toBeNull();
    expect(screen.queryByText(HOME_COPY.empty.line, HIDDEN)).toBeNull();

    await home.land();

    expect(await screen.findByText('Your games · 0')).toBeTruthy();
  });
});

describe('once every read has finished', () => {
  it('reveals everything together — never FOR YOU first, though its reads land first', async () => {
    anasHome();
    const yourThings = hold(YOUR_THINGS);
    const forYou = hold(FOR_YOU);
    await onHome();

    await forYou.land();
    expect(forYouHeading()).toBeNull();
    expect(skeletonOf('for-you')).not.toBeNull();

    await yourThings.land();

    expect(screen.getByText('Your games · 1')).toBeTruthy();
    expect(forYouHeading()).not.toBeNull();
    expect(lineTitles()).toEqual([GROUPS, LEVEL, TOP]);
    expect(envelope()).not.toBeNull();
    pastTheFade();
    expect(skeletonOf('your-games')).toBeNull();
    expect(skeletonOf('for-you')).toBeNull();
  });

  it('counts a read that failed once and is retrying as finished', async () => {
    anasHome();
    // The bell's read is refused once, and Query asks again a moment later: Home does not wait for it.
    const notices = servedBody(transport.answerNow('GET', NOTICES_PATH) as Response);
    let asked = 0;
    transport.on('GET', NOTICES_PATH, () => {
      asked += 1;
      return asked === 1 ? errorResponse(503, 'unavailable') : json(notices);
    });
    await onHome();

    expect(bell().props.accessibilityLabel).toBe('Recent notifications');
    expect(screen.getByText('Your games · 1')).toBeTruthy();
    expect(forYouHeading()).not.toBeNull();

    // The retry lands, and its number comes in with it.
    await act(() => jest.advanceTimersByTimeAsync(RETRY));
    await settle();
    expect(bell().props.accessibilityLabel).toBe('Recent notifications, 3 new');
  });

  it('does not wait for Top 10 behind a Home read that failed once and is retrying', async () => {
    anasHome();
    const home = servedBody(transport.answerNow('GET', HOME_PATH) as Response);
    let asked = 0;
    transport.on('GET', HOME_PATH, () => {
      asked += 1;
      return asked === 1 ? errorResponse(503, 'unavailable') : json(home);
    });
    await onHome();

    // Top 10 waits for the trophy's sport, so it has not set out — and FOR YOU stands without it.
    expect(transport.requestsTo('GET', TOP_TEN_PATH)).toHaveLength(0);
    expect(forYouHeading()).not.toBeNull();
    expect(lineTitles()).toEqual([GROUPS, LEVEL]);
    // Your games is not drawn until its read lands: its own skeleton keeps its place meanwhile, so
    // it never comes in above FOR YOU and pushes it down.
    pastTheFade();
    expect(yourGames()).toBeNull();
    expect(skeletonOf('your-games')).not.toBeNull();
    expect(skeletonOf('for-you')).toBeNull();

    await act(() => jest.advanceTimersByTimeAsync(RETRY));
    await settle();

    expect(screen.getByText('Your games · 1')).toBeTruthy();
    expect(skeletonOf('your-games')).toBeNull();
    await waitFor(() => expect(lineTitles()).toEqual([GROUPS, LEVEL, TOP]));
  });
});

describe('from the ceiling', () => {
  it('reveals your things while FOR YOU keeps its skeleton, then FOR YOU whole as it lands', async () => {
    anasHome();
    const topTen = hold([TOP_TEN_PATH]);
    await onHome();
    act(() => jest.advanceTimersByTime(REVEAL_CEILING));

    expect(screen.getByText('Your games · 1')).toBeTruthy();
    expect(bell().props.accessibilityLabel).toBe('Recent notifications, 3 new');
    expect(envelope()).not.toBeNull();
    expect(forYouHeading()).toBeNull();
    expect(screen.queryByRole('button', { name: new RegExp(`^${GROUPS}`) })).toBeNull();
    expect(skeletonOf('for-you')).not.toBeNull();

    await topTen.land();

    expect(lineTitles()).toEqual([GROUPS, LEVEL, TOP]);
  });

  it('never reveals FOR YOU before your things — though the header’s numbers come as they land', async () => {
    anasHome();
    // Your groups are out: your things are not finished, though Home's read and the bell's are.
    const groups = hold([MY_GROUPS_PATH]);
    await onHome();
    act(() => jest.advanceTimersByTime(REVEAL_CEILING));

    expect(forYouHeading()).toBeNull();
    expect(yourGames()).toBeNull();
    expect(skeletonOf('your-games')).not.toBeNull();
    expect(skeletonOf('for-you')).not.toBeNull();
    // The numbers stop waiting at the ceiling: they sit in the header's slot and push nothing down.
    expect(bell().props.accessibilityLabel).toBe('Recent notifications, 3 new');
    expect(envelope()).not.toBeNull();
    expect(placeOnTrophy()).not.toBeNull();

    await groups.land();

    expect(screen.getByText('Your games · 1')).toBeTruthy();
    expect(forYouHeading()).not.toBeNull();
  });
});

describe('once Home has revealed', () => {
  it('never shimmers again on a return to Home', async () => {
    anasHome();
    await onHome();
    pastTheFade();

    fireEvent.press(bell());
    await waitFor(() => expect(screen).toHavePathname('/notices'));
    hold(EVERY_READ);
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));

    expect(skeletonOf('your-games')).toBeNull();
    expect(skeletonOf('for-you')).toBeNull();
    expect(screen.getByText('Your games · 1')).toBeTruthy();
  });

  it('never shimmers on a pull, though every read is out again', async () => {
    anasHome();
    await onHome();
    pastTheFade();
    hold(EVERY_READ);

    await act(async () => {
      fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');
    });

    expect(skeletonOf('your-games')).toBeNull();
    expect(skeletonOf('for-you')).toBeNull();
    expect(screen.getByText('Your games · 1')).toBeTruthy();
    expect(forYouHeading()).not.toBeNull();
  });
});
