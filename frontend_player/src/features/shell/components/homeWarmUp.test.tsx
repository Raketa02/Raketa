/**
 * **Home's reads set out while the splash plays** — walked through the real route tree
 * ([#874](https://github.com/Raketa02/Raketa/issues/874); PRD #867; ADR-0209 §2, amended 2026-11-24;
 * the loading shimmer log §7, Q18).
 *
 * Each walk is a cold launch through the harness's warmed launch (`launchWarmed`): the session
 * restored as the launch restores it, then the shell's `warmHome` — the step the root layout starts —
 * against this harness's query client, before the tree is rendered. What is asserted is what the
 * player sees and what the server is asked: whether Home opens on its skeleton or whole, and how many
 * times each of Home's reads was sent, early or at all. That the step is started after the session is
 * restored and never awaited is the sequence's own claim, in `bootstrapApp.test.ts`.
 */

import { screen, waitFor } from 'expo-router/testing-library';

import { proposalKeys } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences, savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { lineTitles } from '@/test-support/forYou';
import { homeGame, stubHomeGames } from '@/test-support/home';
import { ADMINISTRATOR_ONLY, CLUB_ID, club } from '@/test-support/officialGroupsServer';
import {
  GATE_USER,
  HOME_PATH,
  HOTTEST_GROUPS_PATH,
  MY_GROUPS_PATH,
  NEW_IN_RAKIETA_PATH,
  NOTICES_PATH,
  PLAYER_ONLY,
  SAME_LEVEL_PATH,
  SAME_VIBE_PATH,
  TOP_TEN_PATH,
  launchWarmed,
  stubGate,
  stubHottestGroups,
  stubMyGroups,
  stubNotices,
  stubProfileOptions,
  stubSameLevel,
  stubTopTen,
  type GateStub,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

const HIDDEN = { includeHiddenElements: true } as const;
const RATINGS_PATH = '/api/v1/ratings';
const ME_PATH = '/api/v1/users/me';

/** Every read Home waits on before it reveals — your things', then FOR YOU's. */
const HOMES_READS = [
  HOME_PATH,
  RATINGS_PATH,
  MY_GROUPS_PATH,
  NOTICES_PATH,
  HOTTEST_GROUPS_PATH,
  SAME_LEVEL_PATH,
  NEW_IN_RAKIETA_PATH,
  SAME_VIBE_PATH,
  TOP_TEN_PATH,
] as const;

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
  id: 'a0000000-0000-4000-8000-000000008741',
  kind: 'PLAYER',
  name: 'Podgórze',
  monogram: { letters: 'Po', colour: 2 },
  sports: ['PADEL'],
  member_count: 4,
  home_club: { id: 'c0000000-0000-4000-8000-000000008741', name: 'Podgórze Padel' },
};

const HOT_GROUP: Wire['HottestGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000008742',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  join_policy: 'ANYONE',
  run_by: 'tomek.k',
  club: { id: 'c0000000-0000-4000-8000-000000008742', name: 'Kazimierz Padel' },
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
  player_id: 'e0000000-0000-4000-8000-000000008743',
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
      player_id: 'e0000000-0000-4000-8000-000000008744',
      nickname: 'ines.d',
      photo_id: null,
      photo_url: null,
      level: 3.4,
      chip: null,
      is_you: false,
    },
  ],
};

let transport: Transport;

/**
 * **Piotr's Home, every read with something to show**: a booked game, three new notices, 7th in
 * padel on the trophy, and three of FOR YOU's lines — Groups heating up, Players at your level and
 * Top 10. `ranking: null` is the same Home with no place anywhere, whose Top 10 opens on the deck's
 * sport instead.
 */
function piotrsHome(
  account: GateStub = {},
  ranking: Wire['HomeResponse']['ranking'] = { sport: 'PADEL', general_place: 7, friends_place: 4 },
) {
  stubGate(transport, { hasPlayerProfile: true, ratings: [RATING], ...account });
  stubMyGroups(transport, [MINE]);
  stubHomeGames(transport, [homeGame()], { ranking });
  stubNotices(transport, [], { newCount: 3 });
  stubHottestGroups(transport, [HOT_GROUP]);
  stubSameLevel(transport, [AT_YOUR_LEVEL]);
  stubTopTen(transport, RANKED);
}

/** The paths one launch's requests went to, Home's reads only, in the order they were sent. */
const homesReadsIn = (requests: readonly { readonly path: string }[]) =>
  requests
    .map((request) => request.path.split('?')[0] ?? request.path)
    .filter((path) => (HOMES_READS as readonly string[]).includes(path));

const skeleton = (part: 'your-games' | 'for-you') =>
  screen.queryByTestId(`${part}-skeleton`, HIDDEN);

/**
 * **Until this holds, and a beat after** — microtasks only, since the warm-up runs before the tree,
 * where no fake clock is advanced. The beat is the turns a read's answer takes to reach the code
 * awaiting it.
 */
async function landed(holds: () => boolean) {
  for (let turn = 0; !holds(); turn += 1) {
    if (turn > 1_000) throw new Error('It never landed.');
    await Promise.resolve();
  }
  for (let turn = 0; turn < 50; turn += 1) await Promise.resolve();
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

describe('a launch headed for the tabs', () => {
  it('sets out every one of Home’s reads before the tree, and Home opens whole — no skeleton, nothing asked twice', async () => {
    piotrsHome();

    const { early } = await launchWarmed(transport);

    expect([...homesReadsIn(early)].sort()).toEqual([...HOMES_READS].sort());
    // Drawn whole from Home's first frame: no part was unread when it mounted.
    expect(screen.getByTestId('home-parts', HIDDEN)).toBeTruthy();
    expect(skeleton('your-games')).toBeNull();
    expect(skeleton('for-you')).toBeNull();
    expect(screen.getByText('Your games · 1')).toBeTruthy();
    expect(lineTitles()).toEqual(['Groups heating up', 'Players at your level', 'Top 10']);
    // The trophy's place waits only on the phone's remembered view, a local read Home makes itself.
    expect(await screen.findByText('#7')).toBeTruthy();

    // Home found every read fresh: each was sent once, by the warm-up — the account's too.
    for (const path of HOMES_READS) expect(transport.requestsTo('GET', path)).toHaveLength(1);
    expect(transport.requestsTo('GET', ME_PATH)).toHaveLength(1);
  });

  it('opens Top 10 on the deck’s sport when the trophy names none — waiting for the ratings, though Home’s read lands first', async () => {
    piotrsHome({}, null);
    const ratings = transport.hold('GET', RATINGS_PATH);

    const launch = launchWarmed(transport);
    await landed(() => queryClient.getQueryData(proposalKeys.home()) !== undefined);
    ratings.land();
    const { early } = await launch;

    expect(homesReadsIn(early)).toContain(TOP_TEN_PATH);
    expect(transport.requestsTo('GET', TOP_TEN_PATH).map((request) => request.path)).toEqual([
      '/api/v1/top-10?prefer=PADEL',
    ]);
    expect(skeleton('for-you')).toBeNull();
    expect(lineTitles()).toContain('Top 10');
    await waitFor(() => expect(screen.getByText('Your games · 1')).toBeTruthy());
    expect(transport.requestsTo('GET', TOP_TEN_PATH)).toHaveLength(1);
  });

  it('warms an account that also runs a club’s groups once the phone says it wore Player last', async () => {
    piotrsHome({
      profiles: { ...PLAYER_ONLY, administers: [{ club_id: CLUB_ID, club_name: 'Ogrody 33' }] },
    });
    await savePhonePreference(GATE_USER.id, 'lastProfile', 'player');

    const { early } = await launchWarmed(transport);

    expect([...homesReadsIn(early)].sort()).toEqual([...HOMES_READS].sort());
    expect(skeleton('your-games')).toBeNull();
    expect(screen).toHavePathname('/');
  });
});

/**
 * **Nothing of Home is read early for an account headed anywhere else** — by the gate's own rule over
 * the account, so the warm-up and the gate never disagree. Each walk reaches its own screen, and
 * none of Home's reads has been sent by then.
 */
describe('a launch headed anywhere but the tabs sends none of Home’s reads before its own screen', () => {
  const walks: readonly {
    readonly name: string;
    readonly account: GateStub;
    readonly lands: string;
    readonly lastProfile?: string;
  }[] = [
    {
      name: 'an account with no nickname yet, to the naming',
      account: { nickname: null },
      lands: '/name',
    },
    {
      name: 'a named account with no Player profile, to the profile steps',
      account: { hasPlayerProfile: false },
      lands: '/tags',
    },
    {
      name: 'an account that only runs a club’s groups, to its area',
      account: { profiles: ADMINISTRATOR_ONLY },
      lands: `/administrator/${CLUB_ID}`,
    },
    {
      name: 'an account that holds no profile, to Start playing',
      account: { profiles: { ...PLAYER_ONLY, acts_as_player: false } },
      lands: '/start-playing',
    },
    {
      name: 'an account with both profiles that wore its club’s last, to the area',
      account: {
        profiles: { ...PLAYER_ONLY, administers: [{ club_id: CLUB_ID, club_name: 'Ogrody 33' }] },
      },
      lastProfile: `administrator:${CLUB_ID}`,
      lands: `/administrator/${CLUB_ID}`,
    },
  ];

  it.each(walks)('$name', async ({ account, lastProfile, lands }) => {
    piotrsHome(account);
    stubProfileOptions(transport);
    club().install(transport);
    if (lastProfile !== undefined) {
      await savePhonePreference(GATE_USER.id, 'lastProfile', lastProfile);
    }

    const { early } = await launchWarmed(transport);

    expect(early).toEqual([]);
    await waitFor(() => expect(screen).toHavePathname(lands));
    expect(homesReadsIn(transport.requests)).toEqual([]);
  });
});

describe('a phone that already knows it is offline', () => {
  it('sends none of Home’s reads early', async () => {
    piotrsHome();

    const { early } = await launchWarmed(transport, { reachability: 'unreachable' });

    expect(early).toEqual([]);
  });
});
