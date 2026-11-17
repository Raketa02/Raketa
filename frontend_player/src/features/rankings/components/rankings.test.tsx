/**
 * **The trophy on Home and the Rankings page, walked through the real route tree**
 * ([#775](https://github.com/Raketa02/Raketa/issues/775)–[#779](https://github.com/Raketa02/Raketa/issues/779),
 * PRD #766; [ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md); the
 * rankings screens §1–§6; the ranking that shows everybody, [#799](https://github.com/Raketa02/Raketa/issues/799),
 * ADR-0204 §2), with only `fetch` faked.
 *
 * Tomek is 7th of 13 in padel at 2,71: Karol just above at 2,75, Zofia just below at 2,69, Inés at the
 * top at 3,40. **Marek, whom he blocked, is 4th** — the real ranking lists him at his true place, and
 * his record reads *This record isn't available* — and Ewa is 5th. He has no squash level,
 * and nobody is ranked in badminton. **Among his friends** (#777) he is 4th of 9 in padel, Ola just
 * above and Kasia just below; no friend of his is listed in any other sport.
 *
 * Every assertion is about what the player can see, or what left the device.
 */

import { onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { FlatList, Image, RefreshControl, StyleSheet } from 'react-native';

import { BLOCKS_COPY, blockRowLabel } from '@/features/blocks/types';
import { FRIENDS_COPY } from '@/features/friends/types';
import { OWN_RECORD_TITLE, RECORD_TITLE, RECORD_UNAVAILABLE } from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { readPhonePreference, savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import {
  GATE_USER,
  OWN_RECORD_SERVED,
  SPORTS_SERVED,
  launchSignedIn,
  ratingGuideAlreadyShown,
  stubGate,
  stubHome,
  stubOwnRecord,
  stubMyGroups,
  stubProfileOptions,
  stubProfileSurface,
  stubRunsInProgress,
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

/** A walk — Rankings, the questionnaire and back — is longer than jest's five seconds. */
const WALK_TIMEOUT = 30_000;

const rankingPath = (sport: Wire['Sport']) => `/api/v1/rankings/${sport}`;
/** The Add friends sheet's groups (#777). */
const FRIENDS_GROUPS_PATH = '/api/v1/friends/groups';
const recordPath = (playerId: string) => `/api/v1/players/${playerId}/record`;
const ASSESSMENTS_PATH = '/api/v1/assessments';
const SQUASH_RUN = '6f708192-a3b4-4c5d-8e6f-708192a3b775';
const stepPath = `${ASSESSMENTS_PATH}/${SQUASH_RUN}`;

function rating(sport: Wire['Sport'], mu: number): Wire['RatingResponse'] {
  return {
    sport,
    mu,
    sigma: 0.7,
    confidence: 24,
    range: { low: mu - 0.7, high: mu + 0.7 },
    band: { name: 'Established', lower: 2.65, upper: 3.85 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-11-07T09:00:00Z',
  };
}

// ---------------------------------------------------------------------------
// The padel list
// ---------------------------------------------------------------------------

function ranked(
  place: number,
  nickname: string,
  level: number,
  over: Partial<Wire['RankedRowSchema']> = {},
): Wire['RankedRowSchema'] {
  return {
    place,
    player_id: `e0000000-0000-4000-8000-0000000775${String(place).padStart(2, '0')}`,
    nickname,
    photo_id: null,
    photo_url: null,
    form: ['WIN', 'WIN', 'LOSS', 'WIN', 'WIN'],
    chip: { kind: 'SAME', places: null },
    level,
    is_you: false,
    ...over,
  };
}

const INES = ranked(1, 'Inés', 3.4, { chip: { kind: 'DOWN', places: 1 } });
const STAS = ranked(2, 'Staś', 3.05, { chip: { kind: 'UP', places: 2 } });
const PIOTR = ranked(3, 'Piotr', 2.95, { chip: { kind: 'NEW', places: null } });
/** Blocked by Tomek: listed at his true place all the same (ADR-0204 §2), his record closed. */
const MAREK = ranked(4, 'Marek', 2.92);
const EWA = ranked(5, 'Ewa', 2.8);
const KAROL = ranked(6, 'Karol', 2.75);
const TOMEK = ranked(7, GATE_USER.nickname ?? 'tomek.k', 2.71, {
  player_id: GATE_USER.id,
  form: ['WIN', 'LOSS', 'WIN'],
  chip: { kind: 'UP', places: 1 },
  is_you: true,
});
const ZOFIA = ranked(8, 'Zofia', 2.69, { chip: { kind: 'DOWN', places: 2 } });
const PADEL_ROWS = [INES, STAS, PIOTR, MAREK, EWA, KAROL, TOMEK, ZOFIA];

const GAP_LINE: Wire['GapLineSchema'] = {
  above: { nickname: 'Karol', gap: 0.04, wins: 3, tied: false },
  below: { nickname: 'Zofia', gap: 0.02 },
  top_of_the_list: false,
};

function listedCard(over: Partial<Wire['PlaceCardSchema']> = {}): Wire['PlaceCardSchema'] {
  return {
    state: 'LISTED',
    results: 14,
    results_to_enter: 5,
    place: 7,
    of: 13,
    level: 2.71,
    chip: { kind: 'UP', places: 1 },
    gap_line: GAP_LINE,
    ...over,
  };
}

function notListed(
  state: Wire['CardState'],
  over: Partial<Wire['PlaceCardSchema']> = {},
): Wire['PlaceCardSchema'] {
  return {
    state,
    results: 0,
    results_to_enter: 5,
    place: null,
    of: null,
    level: null,
    chip: null,
    gap_line: null,
    ...over,
  };
}

function general(
  sport: Wire['Sport'],
  over: Partial<Wire['RankingResponse']> = {},
): Wire['RankingResponse'] {
  return {
    sport,
    view: 'GENERAL',
    card: listedCard(),
    listed: 13,
    podium: [INES, STAS, PIOTR],
    rows: PADEL_ROWS,
    next: null,
    ...over,
  };
}

/** Squash: he has no level there, and three others are listed. */
const SQUASH = (): Wire['RankingResponse'] =>
  general('SQUASH', {
    card: notListed('NO_LEVEL'),
    listed: 3,
    podium: [],
    rows: [],
  });

/** Badminton: nobody listed. */
const BADMINTON = (): Wire['RankingResponse'] =>
  general('BADMINTON', {
    card: notListed('NO_LEVEL'),
    listed: 0,
    podium: [],
    rows: [],
  });

// ---------------------------------------------------------------------------
// Among his friends (#777)
// ---------------------------------------------------------------------------

function friend(
  place: number,
  nickname: string,
  level: number,
  over: Partial<Wire['RankedRowSchema']> = {},
): Wire['RankedRowSchema'] {
  return ranked(place, nickname, level, {
    player_id: `f0000000-0000-4000-8000-0000000777${String(place).padStart(2, '0')}`,
    ...over,
  });
}

const ANIA = friend(1, 'Ania', 3.2, { chip: { kind: 'UP', places: 1 } });
const BARTEK = friend(2, 'Bartek', 3.0);
const OLA = friend(3, 'Ola', 2.8);
const TOMEK_AMONG_FRIENDS = { ...TOMEK, place: 4, chip: { kind: 'SAME' as const, places: null } };
const KASIA = friend(5, 'Kasia', 2.6);
const FRIENDS_ROWS = [
  ANIA,
  BARTEK,
  OLA,
  TOMEK_AMONG_FRIENDS,
  KASIA,
  friend(6, 'Wojtek', 2.5),
  friend(7, 'Ela', 2.4),
  friend(8, 'Jan', 2.3),
  friend(9, 'Iza', 2.1),
];
/** His friends without him — the table under a card that is not his place. */
const ONLY_FRIENDS = FRIENDS_ROWS.filter((row) => !row.is_you);

/** 4th of 9 among his friends: the line names friends, never the strangers between them. */
const FRIENDS_CARD = listedCard({
  place: 4,
  of: 9,
  results_to_enter: 1,
  chip: { kind: 'SAME', places: null },
  gap_line: {
    above: { nickname: 'Ola', gap: 0.09, wins: 2, tied: false },
    below: { nickname: 'Kasia', gap: 0.11 },
    top_of_the_list: false,
  },
});

function friends(
  sport: Wire['Sport'],
  over: Partial<Wire['RankingResponse']> = {},
): Wire['RankingResponse'] {
  return {
    sport,
    view: 'FRIENDS',
    card: FRIENDS_CARD,
    listed: 9,
    podium: [ANIA, BARTEK, OLA],
    rows: FRIENDS_ROWS,
    next: null,
    ...over,
  };
}

/** No friend listed, nor the reader: the card is the page, with nothing below (the screens §4.6). */
const NO_FRIEND = (sport: Wire['Sport']): Wire['RankingResponse'] =>
  friends(sport, {
    card: notListed('NO_FRIEND_LISTED', { results_to_enter: 1 }),
    listed: 0,
    podium: [],
    rows: [],
  });

// ---------------------------------------------------------------------------
// The server
// ---------------------------------------------------------------------------

let transport: Transport;

interface RankingServer {
  /** Answer one sport's General read with this, from now on. */
  readonly answer: (sport: Wire['Sport'], read: Wire['RankingResponse']) => void;
  /** Answer one sport's Friends read with this, from now on (#777). */
  readonly answerFriends: (sport: Wire['Sport'], read: Wire['RankingResponse']) => void;
}

/**
 * **Tomek, set up long ago and rated in padel and tennis**, with Home's trophy as given, every sport's
 * General and Friends as above, and the records a row opens.
 */
function rankingServer({
  trophy = { sport: 'PADEL', general_place: 7, friends_place: 4 },
  ratings = [rating('PADEL', 2.71), rating('TENNIS', 3.1)],
}: {
  readonly trophy?: Wire['HomeRankingSchema'] | null;
  readonly ratings?: readonly Wire['RatingResponse'][];
} = {}): RankingServer {
  stubGate(transport, { ratings: [...ratings], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  stubHome(transport, { ranking: trophy });
  stubOwnRecord(transport, OWN_RECORD_SERVED);
  // The Add friends sheet's groups (#777): none, unless a walk says otherwise.
  transport.on('GET', FRIENDS_GROUPS_PATH, () =>
    json<Wire['GroupsToAddFromResponse']>({ groups: [] }),
  );

  const reads = new Map<Wire['Sport'], Wire['RankingResponse']>([
    ['PADEL', general('PADEL')],
    ['TENNIS', general('TENNIS', { rows: [], podium: [], listed: 0 })],
    ['SQUASH', SQUASH()],
    ['BADMINTON', BADMINTON()],
  ]);
  const friendsReads = new Map<Wire['Sport'], Wire['RankingResponse']>([
    ['PADEL', friends('PADEL')],
    ['TENNIS', NO_FRIEND('TENNIS')],
    ['SQUASH', NO_FRIEND('SQUASH')],
    ['BADMINTON', NO_FRIEND('BADMINTON')],
  ]);
  for (const sport of ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'] as const) {
    transport.on('GET', rankingPath(sport), (request) =>
      json(request.path.includes('view=FRIENDS') ? friendsReads.get(sport)! : reads.get(sport)!),
    );
  }

  for (const row of PADEL_ROWS.filter((one) => !one.is_you && one !== MAREK)) {
    transport.on('GET', recordPath(row.player_id), () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: 'NONE',
        can_add_friend: true,
        nickname: row.nickname,
        photos: [],
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: row.level, band: 'Established' }],
        reliability: servedReliability({ player_score: 96, is_new: false }),
      }),
    );
  }
  // A block either way closes the record, with the one refusal that names nothing.
  transport.on('GET', recordPath(MAREK.player_id), () => errorResponse(404, 'record_unavailable'));

  return {
    answer: (sport, read) => reads.set(sport, read),
    answerFriends: (sport, read) => friendsReads.set(sport, read),
  };
}

beforeEach(async () => {
  transport = installTransport();
  await ratingGuideAlreadyShown();
});

afterEach(async () => {
  onlineManager.setOnline(true);
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

// ---------------------------------------------------------------------------
// Walking
// ---------------------------------------------------------------------------

const trophy = () => screen.getByTestId('ranking-trophy');
const rankingReads = (sport: Wire['Sport']) => transport.requestsTo('GET', rankingPath(sport));
const viewReads = (sport: Wire['Sport'], view: Wire['RankingView']) =>
  rankingReads(sport).filter((request) => request.url.includes(`view=${view}`));

/** Home, then the trophy, then the page for this sport. */
async function openRankings(sport: Wire['Sport'] = 'PADEL') {
  await launchSignedIn();
  fireEvent.press(await screen.findByTestId('ranking-trophy'));
  await waitFor(() => expect(screen).toHavePathname('/rankings'));
  await waitFor(() => expect(rankingReads(sport).length).toBeGreaterThan(0));
}

/** The pill in the page's header, and the bar it unfolds into. */
const pill = () => screen.getByTestId('sport-filter-header');
function unfoldThePill(current: string) {
  fireEvent.press(within(pill()).getByRole('button', { name: `Sport: ${current}` }));
  act(() => jest.advanceTimersByTime(theme.motion.unfold));
}
function barOptions(): string[] {
  return within(screen.getByTestId('sport-bar'))
    .getAllByRole('button')
    .map((option) => option.props.accessibilityLabel as string);
}

/** Everything a text says, its nested texts included — the gap line is one text of several runs. */
function said(node: { readonly props: { readonly children?: unknown } }): string {
  const read = (children: unknown): string => {
    if (typeof children === 'string' || typeof children === 'number') return String(children);
    if (Array.isArray(children)) return children.map(read).join('');
    if (children !== null && typeof children === 'object' && 'props' in children) {
      return read((children as { props: { children?: unknown } }).props.children);
    }
    return '';
  };
  return read(node.props.children);
}

/** The chip's drawing is hidden from a listener: the row names it. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;

const rowOf = (row: Wire['RankedRowSchema']) => screen.getByTestId(`ranked-row-${row.player_id}`);
/** Every row the list draws, best first. */
const listedRows = () => screen.queryAllByTestId(/^ranked-row-/);

/** A row's form, read off the squares it draws — `RunOfForm`'s mint and grey. */
function formOf(row: Wire['RankedRowSchema']): string[] {
  return within(rowOf(row))
    .UNSAFE_getAllByType(require('react-native').View)
    .map((node) => StyleSheet.flatten(node.props.style) ?? {})
    .filter((style) => style.width === theme.size.recordSquare)
    .map((style) => (style.backgroundColor === theme.color.mint ? 'WIN' : 'LOSS'));
}

// ---------------------------------------------------------------------------
// Home's trophy
// ---------------------------------------------------------------------------

describe('the trophy on Home', () => {
  it('reads #7 in the corner, right of the bell, and opens Rankings on its sport with the Home tab lit', async () => {
    rankingServer({ trophy: { sport: 'TENNIS', general_place: 7, friends_place: null } });
    await launchSignedIn();

    await waitFor(() => expect(within(trophy()).getByText('#7')).toBeTruthy());
    expect(trophy().props.accessibilityLabel).toBe('Rankings, 7th in tennis');
    // The trophy took the corner from the bell, which stands beside it (#816, ADR-0205 §2); the
    // header's order is the shell's suite's.
    expect(screen.getByRole('button', { name: 'Recent notifications' })).toBeTruthy();

    fireEvent.press(trophy());

    await waitFor(() => expect(screen).toHavePathname('/rankings'));
    await waitFor(() => expect(rankingReads('TENNIS')).toHaveLength(1));
    expect(rankingReads('TENNIS')[0]!.url).toContain('view=GENERAL');
    expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();
  });

  it('draws no number with no place, and is still a button that opens Rankings', async () => {
    rankingServer({ trophy: { sport: 'PADEL', general_place: null, friends_place: null } });
    await launchSignedIn();

    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/home').length).toBe(1));
    expect(within(trophy()).queryByText(/^#/)).toBeNull();
    expect(trophy().props.accessibilityLabel).toBe('Rankings');

    fireEvent.press(trophy());

    await waitFor(() => expect(rankingReads('PADEL')).toHaveLength(1));
  });

  it('goes back to Home from the page', async () => {
    rankingServer();
    await openRankings();

    fireEvent.press(await screen.findByLabelText('Back to Home'));

    await waitFor(() => expect(screen).toHavePathname('/'));
  });
});

// ---------------------------------------------------------------------------
// The header and the sport
// ---------------------------------------------------------------------------

describe('the header', () => {
  it('reads Rankings, Competitive games only, and the sport pill', async () => {
    rankingServer();
    await openRankings();

    expect(await screen.findByText('Rankings')).toBeTruthy();
    expect(screen.getByText('Competitive games only')).toBeTruthy();
    expect(within(pill()).getByRole('button', { name: 'Sport: Padel' })).toBeTruthy();
  });

  it('offers all four sports, rated first, and switching sport reads that one', async () => {
    rankingServer({ ratings: [rating('SQUASH', 2.4), rating('PADEL', 2.71)] });
    await openRankings();
    await screen.findByText('7th');

    unfoldThePill('Padel');

    // The current sport last, the others in the order handed: rated (padel, squash), then the rest.
    expect(barOptions()).toEqual(['Squash', 'Tennis', 'Badminton', 'Padel']);

    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Tennis' }),
    );

    await waitFor(() => expect(rankingReads('TENNIS')).toHaveLength(1));
    expect(await screen.findByText('Nobody ranked in tennis yet')).toBeTruthy();
    expect(within(pill()).getByRole('button', { name: 'Sport: Tennis' })).toBeTruthy();
  });
});

describe('which sport the page opens on', () => {
  it('is the deck’s last sport when the trophy names none', async () => {
    rankingServer({
      trophy: null,
      ratings: [rating('PADEL', 2.71), rating('SQUASH', 2.4)],
    });
    await savePhonePreference(GATE_USER.id, 'lastSport', 'squash');
    await launchSignedIn();

    fireEvent.press(await screen.findByTestId('ranking-trophy'));

    await waitFor(() => expect(rankingReads('SQUASH')).toHaveLength(1));
    expect(rankingReads('PADEL')).toHaveLength(0);
  });

  it('is the trophy’s sport even when the trophy is tapped before Home has answered', async () => {
    rankingServer({ ratings: [rating('PADEL', 2.71), rating('TENNIS', 3.1)] });
    let answer = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('GET', '/api/v1/home', async () => {
      await held;
      return json<Wire['HomeResponse']>({
        read_at: '2026-11-08T08:00:00Z',
        needing_you: 0,
        games: [],
        friend_requests: [],
        friends_games: [],
        level_asks: [],
        ranking: { sport: 'TENNIS', general_place: 7, friends_place: null },
      });
    });
    await launchSignedIn();

    fireEvent.press(await screen.findByTestId('ranking-trophy'));
    await waitFor(() => expect(screen).toHavePathname('/rankings'));
    // Nothing is read for the deck's sport while the trophy's is still on its way.
    expect(rankingReads('PADEL')).toHaveLength(0);

    await act(async () => answer());

    await waitFor(() => expect(rankingReads('TENNIS')).toHaveLength(1));
    expect(rankingReads('PADEL')).toHaveLength(0);
  });

  it('is padel with no level anywhere', async () => {
    rankingServer({ trophy: null, ratings: [] });
    await launchSignedIn();

    fireEvent.press(await screen.findByTestId('ranking-trophy'));

    await waitFor(() => expect(rankingReads('PADEL')).toHaveLength(1));
  });
});

// ---------------------------------------------------------------------------
// The place card
// ---------------------------------------------------------------------------

describe('the place card', () => {
  it('listed: YOUR PLACE, 7th of 13, the level, the chip and its words, and the gap line', async () => {
    rankingServer();
    await openRankings();

    const card = within(await screen.findByTestId('place-card'));
    expect(card.getByText('YOUR PLACE')).toBeTruthy();
    expect(card.getByText('7th')).toBeTruthy();
    expect(card.getByText('of 13')).toBeTruthy();
    expect(card.getByText('2,71')).toBeTruthy();
    expect(card.getByTestId('rank-chip-UP', HIDDEN_TOO)).toBeTruthy();
    expect(card.getByText('up this week')).toBeTruthy();
    expect(said(screen.getByTestId('gap-line'))).toBe(
      '0,04 behind Karol · about 3 wins close it · Zofia is 0,02 behind you',
    );
  });

  it.each<[string, Partial<Wire['PlaceCardSchema']>, string]>([
    [
      'one win',
      {
        gap_line: {
          ...GAP_LINE,
          above: { nickname: 'Karol', gap: 0.04, wins: 1, tied: false },
        },
      },
      '0,04 behind Karol · one win closes it · Zofia is 0,02 behind you',
    ],
    [
      'more than five, left out',
      {
        gap_line: {
          ...GAP_LINE,
          above: { nickname: 'Karol', gap: 0.31, wins: null, tied: false },
        },
      },
      '0,31 behind Karol · Zofia is 0,02 behind you',
    ],
    [
      'level with the player above',
      { gap_line: { ...GAP_LINE, above: { nickname: 'Ewa', gap: 0, wins: null, tied: true } } },
      'Level with Ewa · one win puts you ahead · Zofia is 0,02 behind you',
    ],
    [
      'the player below level with you',
      { gap_line: { ...GAP_LINE, below: { nickname: 'Zofia', gap: 0 } } },
      '0,04 behind Karol · about 3 wins close it · Zofia is level with you',
    ],
    [
      'last place',
      { gap_line: { ...GAP_LINE, below: null } },
      '0,04 behind Karol · about 3 wins close it',
    ],
    [
      'first place',
      { place: 1, gap_line: { above: null, below: null, top_of_the_list: true } },
      'Top of the list',
    ],
  ])('the gap line: %s', async (_case, card, line) => {
    const server = rankingServer();
    server.answer('PADEL', general('PADEL', { card: listedCard(card) }));
    await openRankings();

    expect(said(await screen.findByTestId('gap-line'))).toBe(line);
  });

  it.each<[string, Wire['ChipSchema'], string, string]>([
    ['down', { kind: 'DOWN', places: 1 }, 'rank-chip-DOWN', 'down this week'],
    ['no change', { kind: 'SAME', places: null }, 'rank-chip-SAME', 'no change this week'],
    ['new', { kind: 'NEW', places: null }, 'rank-chip-NEW', 'this week'],
  ])('listed, the chip %s, with its words', async (_case, chip, testID, words) => {
    const server = rankingServer();
    server.answer('PADEL', general('PADEL', { card: listedCard({ chip }) }));
    await openRankings();

    const card = within(await screen.findByTestId('place-card'));
    expect(card.getByTestId(testID, HIDDEN_TOO)).toBeTruthy();
    expect(card.getByText(words)).toBeTruthy();
  });

  it('draws no switch: no Show me in General, no Hidden from General — only General | Friends (#799)', async () => {
    rankingServer();
    await openRankings();

    expect(said(await screen.findByTestId('gap-line'))).toContain('behind Karol');
    expect(screen.queryByRole('switch')).toBeNull();
    expect(screen.queryByText('Hidden from General')).toBeNull();
    expect(screen.queryByText(/^Show me/)).toBeNull();
    expect(screen.queryByTestId('hidden-from-general')).toBeNull();
  });

  it.each<[string, Wire['PlaceCardSchema'], string]>([
    [
      'fewer than 5 results',
      notListed('NEEDS_RESULTS', { results: 2 }),
      '2 of 5 games — 3 more competitive padel games put you on the list',
    ],
    [
      'one result to go',
      notListed('NEEDS_RESULTS', { results: 4 }),
      '4 of 5 games — 1 more competitive padel game puts you on the list',
    ],
    [
      'off the list',
      notListed('OFF_THE_LIST', { results: 9 }),
      'Off the list — no competitive padel game in 90 days. Your next one puts you back.',
    ],
  ])('not listed: %s', async (_case, card, line) => {
    const server = rankingServer();
    server.answer('PADEL', general('PADEL', { card }));
    await openRankings();

    expect(said(await screen.findByTestId('not-listed-line'))).toBe(line);
    expect(screen.queryByTestId('place-card')).toBeNull();
    // A light card, one line, no button.
    expect(screen.queryByRole('button', { name: /^Get your/ })).toBeNull();
    // The list is drawn under it all the same.
    expect(listedRows().length).toBeGreaterThan(0);
  });

  it(
    'no level: Get your squash level starts its questionnaire, and the pass returns to Rankings on squash',
    async () => {
      const server = rankingServer();
      let ratings = [rating('PADEL', 2.71), rating('TENNIS', 3.1)];
      transport.on('GET', '/api/v1/ratings', () => json<Wire['RatingsResponse']>({ ratings }));
      const question: Wire['QuestionResponse'] = {
        id: 'q-played-squash',
        category: 'Recent activity',
        tier: null,
        situation: 'Before anything else',
        text: 'Have you played squash before?',
        qualifier: 'Any level counts',
        options: [
          { id: 'never', text: 'Never played' },
          { id: 'regular', text: 'I play most weeks' },
        ],
      };
      const opening: Wire['AssessmentStepResponse'] = {
        assessment_id: SQUASH_RUN,
        status: 'in_progress',
        questions_asked: 0,
        transcript: [],
        question,
      };
      const stopped: Wire['AssessmentStepResponse'] = {
        ...opening,
        questions_asked: 1,
        transcript: [{ question, option_id: 'regular' }],
        question: null,
        result: null,
      };
      transport.on('POST', ASSESSMENTS_PATH, () => {
        stubRunsInProgress(transport, [{ assessment_id: SQUASH_RUN, sport: 'SQUASH' }]);
        return json(opening, 201);
      });
      transport.on('GET', stepPath, () => json(opening));
      transport.on('POST', `${stepPath}/answers`, () => json(stopped));
      transport.on('POST', `${stepPath}/completion`, () => {
        stubRunsInProgress(transport, []);
        ratings = [...ratings, rating('SQUASH', 2.4)];
        // The server now reads him as rated, with no result yet.
        server.answer('SQUASH', general('SQUASH', { card: notListed('NEEDS_RESULTS'), listed: 3 }));
        return json<Wire['AssessmentStepResponse']>({
          ...stopped,
          status: 'completed',
          result: {
            mu: 2.4,
            sigma: 0.7,
            confidence: 24,
            confidence_ceiling: 30,
            range: { low: 1.7, high: 3.1 },
            band: { name: 'Developing', lower: 1.55, upper: 2.65 },
            status: 'initial_estimate',
            questions_asked: 1,
            engine_version: 'racketskill-v3',
            calibration_priority: 'standard',
          },
        });
      });
      transport.on('POST', `${stepPath}/abandonment`, () => noContent());

      await openRankings();
      await screen.findByText('7th');
      unfoldThePill('Padel');
      fireEvent.press(
        within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Squash' }),
      );
      expect(said(await screen.findByTestId('not-listed-line'))).toBe(
        'No squash level yet — get one, then 5 competitive games put you on the list',
      );

      fireEvent.press(screen.getByRole('button', { name: 'Get your squash level' }));

      await waitFor(() => expect(screen).toHavePathname(`/question/${SQUASH_RUN}`));
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH)[0]!.body).toEqual({ sport: 'SQUASH' });
      fireEvent.press(await screen.findByLabelText('I play most weeks'));
      fireEvent.press(screen.getByLabelText('Confirm answer'));
      await waitFor(() => expect(screen).toHavePathname(`/review/${SQUASH_RUN}`));
      fireEvent.press(await screen.findByLabelText('Get my Squash level'));
      await waitFor(() => expect(screen).toHavePathname(`/result/${SQUASH_RUN}`), {
        timeout: 4000,
      });

      fireEvent.press(await screen.findByLabelText('Back to Rankings'));

      // Back on Rankings, on squash, read again: the card now counts his games.
      await waitFor(() => expect(screen).toHavePathname('/rankings'), { timeout: 4000 });
      await waitFor(() =>
        expect(said(screen.getByTestId('not-listed-line'))).toBe(
          '0 of 5 games — 5 more competitive squash games put you on the list',
        ),
      );
      expect(within(pill()).getByRole('button', { name: 'Sport: Squash' })).toBeTruthy();
      expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();

      // And Home is beneath it.
      fireEvent.press(screen.getByLabelText('Back to Home'));
      await waitFor(() => expect(screen).toHavePathname('/'));
    },
    WALK_TIMEOUT,
  );
});

// ---------------------------------------------------------------------------
// The podium and the list
// ---------------------------------------------------------------------------

describe('the podium', () => {
  it('stands the first three rows the reader sees: first in the middle, second left, third right', async () => {
    rankingServer();
    await openRankings();

    const podium = await screen.findByTestId('podium');
    const steps = within(podium).getAllByRole('button');
    expect(steps.map((step) => step.props.testID)).toEqual([
      'podium-second',
      'podium-first',
      'podium-third',
    ]);
    expect(within(screen.getByTestId('podium-first')).getByText('Inés')).toBeTruthy();
    expect(within(screen.getByTestId('podium-first')).getByText('3,40')).toBeTruthy();
    expect(within(screen.getByTestId('podium-second')).getByText('Staś')).toBeTruthy();
    expect(within(screen.getByTestId('podium-third')).getByText('Piotr')).toBeTruthy();
  });

  it('labels each step with its true place', async () => {
    rankingServer();
    await openRankings();

    await screen.findByTestId('podium');
    expect(within(screen.getByTestId('podium-first')).getByText('1')).toBeTruthy();
    expect(within(screen.getByTestId('podium-second')).getByText('2')).toBeTruthy();
    expect(within(screen.getByTestId('podium-third')).getByText('3')).toBeTruthy();
  });

  it('is not drawn with fewer than three rows: the list shows alone', async () => {
    const server = rankingServer();
    server.answer('PADEL', general('PADEL', { podium: [], rows: [INES, TOMEK], listed: 2 }));
    await openRankings();

    expect(await screen.findAllByTestId(/^ranked-row-/)).toHaveLength(2);
    expect(screen.queryByTestId('podium')).toBeNull();
  });
});

describe('the rows', () => {
  it('draw every place — coral for 1–3, grey after, the player he blocked among them (#799)', async () => {
    rankingServer();
    await openRankings();
    await screen.findAllByTestId(/^ranked-row-/);

    const places = screen
      .getAllByTestId(/^ranked-place-/)
      .map((node) => [node.props.children as number, StyleSheet.flatten(node.props.style).color]);
    expect(places).toEqual([
      [1, theme.color.coralInk],
      [2, theme.color.coralInk],
      [3, theme.color.coralInk],
      [4, theme.color.muted],
      [5, theme.color.muted],
      [6, theme.color.muted],
      [7, theme.color.muted],
      [8, theme.color.muted],
    ]);
    expect(within(rowOf(MAREK)).getByText('Marek')).toBeTruthy();
  });

  it('draw the form as the record’s squares, oldest first and never padded', async () => {
    rankingServer();
    await openRankings();
    await screen.findAllByTestId(/^ranked-row-/);

    expect(formOf(INES)).toEqual(['WIN', 'WIN', 'LOSS', 'WIN', 'WIN']);
    expect(formOf(TOMEK)).toEqual(['WIN', 'LOSS', 'WIN']);
  });

  it('draw every chip: up and down with their counts, the same, and New', async () => {
    rankingServer();
    await openRankings();
    await screen.findAllByTestId(/^ranked-row-/);

    const chip = (row: Wire['RankedRowSchema'], kind: Wire['ChipKind']) =>
      within(within(rowOf(row)).getByTestId(`rank-chip-${kind}`, HIDDEN_TOO));
    // ▼ 1 and ▲ 2 — the triangles drawn, the counts mono beside them.
    expect(chip(INES, 'DOWN').getByTestId('rank-chip-down', HIDDEN_TOO)).toBeTruthy();
    expect(chip(INES, 'DOWN').getByText('1', HIDDEN_TOO)).toBeTruthy();
    expect(chip(STAS, 'UP').getByTestId('rank-chip-up', HIDDEN_TOO)).toBeTruthy();
    expect(chip(STAS, 'UP').getByText('2', HIDDEN_TOO)).toBeTruthy();
    expect(chip(PIOTR, 'NEW').getByText('New', HIDDEN_TOO)).toBeTruthy();
    // — : a drawn rule, and no count.
    expect(chip(KAROL, 'SAME').getByTestId('rank-chip-same', HIDDEN_TOO)).toBeTruthy();
    expect(chip(KAROL, 'SAME').queryByText(/\d/, HIDDEN_TOO)).toBeNull();
  });

  it('read You on the reader’s own row, tinted', async () => {
    rankingServer();
    await openRankings();
    await screen.findAllByTestId(/^ranked-row-/);

    const own = rowOf(TOMEK);
    expect(within(own).getByText('You')).toBeTruthy();
    expect(within(own).queryByText(TOMEK.nickname)).toBeNull();
    expect(StyleSheet.flatten(own.props.style).backgroundColor).toBe(theme.color.coralSoft);
    expect(StyleSheet.flatten(rowOf(KAROL).props.style).backgroundColor).toBeUndefined();
    expect(within(own).getByText('2,71')).toBeTruthy();
  });
});

describe('an empty sport', () => {
  it('reads Nobody ranked in badminton yet, and draws no podium and no list', async () => {
    rankingServer();
    await openRankings();
    await screen.findByText('7th');

    unfoldThePill('Padel');
    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Badminton' }),
    );

    expect(await screen.findByText('Nobody ranked in badminton yet')).toBeTruthy();
    expect(screen.queryByTestId('podium')).toBeNull();
    expect(listedRows()).toHaveLength(0);
  });
});

describe('a face opens the record', () => {
  it('opens a stranger’s record from their row, on the page’s sport', async () => {
    rankingServer();
    await openRankings();

    fireEvent.press(await screen.findByTestId(`ranked-row-${KAROL.player_id}`));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', recordPath(KAROL.player_id))).toHaveLength(1),
    );
    expect(transport.requestsTo('GET', recordPath(KAROL.player_id))[0]!.url).toContain(
      'sport=PADEL',
    );
  });

  it('opens a record from a podium step', async () => {
    rankingServer();
    await openRankings();

    fireEvent.press(await screen.findByTestId('podium-first'));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', recordPath(INES.player_id))).toHaveLength(1),
    );
  });

  it('reads This record isn’t available from the row of a player he blocked (#799)', async () => {
    rankingServer();
    await openRankings();

    fireEvent.press(await screen.findByTestId(`ranked-row-${MAREK.player_id}`));

    expect(await screen.findByText(RECORD_UNAVAILABLE)).toBeTruthy();
    expect(transport.requestsTo('GET', recordPath(MAREK.player_id))).toHaveLength(1);
    // One line and nothing else: no foot, no Block, no Add friend.
    expect(screen.queryByTestId('record-foot')).toBeNull();
    expect(screen.queryByRole('button', { name: FRIENDS_COPY.record.add })).toBeNull();
  });

  it('opens the reader’s own record from their own row', async () => {
    rankingServer();
    await openRankings();

    fireEvent.press(await screen.findByTestId(`ranked-row-${TOMEK.player_id}`));

    expect(await screen.findByText(OWN_RECORD_TITLE)).toBeTruthy();
    expect(transport.requestsTo('GET', recordPath(TOMEK.player_id))).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// A stranger's record from the ranking (#779; the screens §6)
// ---------------------------------------------------------------------------

const REQUESTS_PATH = '/api/v1/friends/requests';
const asked = () => transport.requestsTo('POST', REQUESTS_PATH).map((request) => request.body);

/** Piotr, 3rd in padel, whom Tomek shares no group with — anybody may open his record (ADR-0204 §2). */
function piotrsRecord(
  over: Partial<Wire['PlayerRecordResponse']> = {},
): Wire['PlayerRecordResponse'] {
  return {
    is_self: false,
    relation: 'NONE',
    can_add_friend: true,
    nickname: PIOTR.nickname,
    photos: [],
    area_code: 'A+050612+0019938',
    social_tags: [],
    sports: [{ sport: 'PADEL', level: PIOTR.level, band: 'Established' }],
    reliability: servedReliability({ player_score: 96, is_new: false }),
    ...over,
  };
}

/**
 * **The friends route, faked as far as a stranger's request goes**: a request is `SENT`, and his
 * record says so on its next read — or, once he has turned *Show me to new people* off since the
 * record was read, the request is refused with the one unnamed code and his record with the one
 * refusal (ADR-0204 §2).
 */
function strangerServer({
  record = piotrsRecord(),
  switchedOff = false,
}: { readonly record?: Wire['PlayerRecordResponse']; readonly switchedOff?: boolean } = {}) {
  let relation: Wire['FriendRelation'] = 'NONE';
  let closed = false;
  transport.on('POST', REQUESTS_PATH, () => {
    if (switchedOff) {
      closed = true;
      return errorResponse(404, 'player_unavailable');
    }
    relation = 'SENT';
    return json<Wire['RelationResponse']>({ relation });
  });
  transport.on('GET', recordPath(PIOTR.player_id), () =>
    closed
      ? errorResponse(404, 'record_unavailable')
      : json({ ...record, relation, can_add_friend: relation === 'NONE' }),
  );
}

/** Three photos, in his own order — the first is the header's. */
const PIOTRS_PHOTOS: Wire['RecordPhotoSchema'][] = [
  { photo_id: 'p0000000-0000-4000-8000-000000079901', photo_url: 'https://photos.test/piotr-1' },
  { photo_id: 'p0000000-0000-4000-8000-000000079902', photo_url: 'https://photos.test/piotr-2' },
  { photo_id: 'p0000000-0000-4000-8000-000000079903', photo_url: 'https://photos.test/piotr-3' },
];

/** The photos a carousel draws, in order, read off their images. */
function carouselPhotos(): string[] {
  return within(screen.getByTestId('record-photos', HIDDEN_TOO))
    .UNSAFE_getAllByType(Image)
    .map((image) => (image.props.source as { uri: string }).uri);
}

/** Piotr's record, opened from his step on the podium. */
async function openPiotrsRecord() {
  await openRankings();
  fireEvent.press(await screen.findByTestId('podium-third'));
  expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
  // The record's answer drawn: its foot.
  await screen.findByRole('button', { name: blockRowLabel(PIOTR.nickname) });
}

const foot = () => within(screen.getByTestId('record-foot'));

describe('a stranger’s record from the ranking (#779)', () => {
  it('offers Add friend beside Block, and sends it from the ranking with the page’s sport', async () => {
    rankingServer();
    strangerServer();
    await openPiotrsRecord();

    expect(foot().getByRole('button', { name: FRIENDS_COPY.record.add })).toBeTruthy();
    expect(foot().getByText(BLOCKS_COPY.row.block)).toBeTruthy();

    fireEvent.press(foot().getByRole('button', { name: FRIENDS_COPY.record.add }));

    await waitFor(() => expect(asked()).toHaveLength(1));
    // The ranking, its sport, and no group: the page shows none.
    expect(asked()[0]).toEqual({
      player_id: PIOTR.player_id,
      made_from: 'RANKING',
      sport: 'PADEL',
    });
    // The record read again, and its foot is the server's next answer.
    expect(await screen.findByRole('button', { name: FRIENDS_COPY.record.sent })).toBeTruthy();
    expect(transport.requestsTo('GET', recordPath(PIOTR.player_id))).toHaveLength(2);
    // Block still beside it, and Unblock nowhere.
    expect(foot().getByRole('button', { name: blockRowLabel(PIOTR.nickname) })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^Unblock/ })).toBeNull();
  });

  it('draws all of a stranger’s photos, in his order, with Add friend beside Block (#799)', async () => {
    rankingServer();
    strangerServer({
      record: piotrsRecord({
        photos: PIOTRS_PHOTOS,
        photo_id: PIOTRS_PHOTOS[0]!.photo_id,
        photo_url: PIOTRS_PHOTOS[0]!.photo_url,
        review: 'allowed',
      }),
    });
    await openPiotrsRecord();

    expect(carouselPhotos()).toEqual([
      'https://photos.test/piotr-1',
      'https://photos.test/piotr-2',
      'https://photos.test/piotr-3',
    ]);
    expect(foot().getByRole('button', { name: FRIENDS_COPY.record.add })).toBeTruthy();
  });

  it('draws no carousel for a stranger with no photo', async () => {
    rankingServer();
    strangerServer();
    await openPiotrsRecord();

    expect(screen.queryByTestId('record-photos', HIDDEN_TOO)).toBeNull();
  });

  it('asks with no limit: request after request is sent, and no limit sentence is said (#799)', async () => {
    rankingServer();
    strangerServer();
    await openPiotrsRecord();

    fireEvent.press(foot().getByRole('button', { name: FRIENDS_COPY.record.add }));

    expect(await screen.findByRole('button', { name: FRIENDS_COPY.record.sent })).toBeTruthy();
    expect(screen.queryByText(/requests to new people today/)).toBeNull();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(Object.keys(FRIENDS_COPY.refused)).not.toContain('daily_request_limit');
  });

  it('re-reads the record quietly when he turned Show me to new people off since — and it reads This record isn’t available (#799)', async () => {
    rankingServer();
    strangerServer({ switchedOff: true });
    await openPiotrsRecord();

    fireEvent.press(foot().getByRole('button', { name: FRIENDS_COPY.record.add }));

    await waitFor(() => expect(asked()).toHaveLength(1));
    // Nothing said about the refusal: the record read again is the answer.
    expect(await screen.findByText(RECORD_UNAVAILABLE)).toBeTruthy();
    expect(transport.requestsTo('GET', recordPath(PIOTR.player_id))).toHaveLength(2);
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.queryByTestId('record-foot')).toBeNull();
  });

  it('draws Block alone, full width, where the record says no request may be sent — and never Unblock', async () => {
    rankingServer();
    transport.on('GET', recordPath(PIOTR.player_id), () =>
      json(piotrsRecord({ can_add_friend: false })),
    );
    await openPiotrsRecord();

    expect(foot().getByRole('button', { name: blockRowLabel(PIOTR.nickname) })).toBeTruthy();
    expect(foot().queryByRole('button', { name: FRIENDS_COPY.record.add })).toBeNull();
    expect(screen.queryByText(/^Unblock/)).toBeNull();
    expect(screen.queryByRole('button', { name: /^Unblock/ })).toBeNull();
  });

  it('reads the record’s one refusal where the server refuses it — a block, or Show me to new people off', async () => {
    rankingServer();
    transport.on('GET', recordPath(PIOTR.player_id), () =>
      errorResponse(404, 'record_unavailable'),
    );
    await openRankings();

    fireEvent.press(await screen.findByTestId('podium-third'));

    expect(await screen.findByText(RECORD_UNAVAILABLE)).toBeTruthy();
    expect(screen.queryByTestId('record-foot')).toBeNull();
    expect(screen.queryByRole('button', { name: /^(Block|Unblock) / })).toBeNull();
  });
});

/** The page's own pull — Home's is beneath it in the stack. */
const pageRefresh = () =>
  within(screen.getByTestId('rankings-page')).UNSAFE_getByType(RefreshControl);

describe('reading the page', () => {
  it('reads it again on a pull', async () => {
    const server = rankingServer();
    await openRankings();
    await screen.findByText('7th');
    server.answer('PADEL', general('PADEL', { card: listedCard({ place: 6, of: 13 }) }));

    await act(async () => {
      fireEvent(pageRefresh(), 'refresh');
    });

    await waitFor(() => expect(rankingReads('PADEL')).toHaveLength(2));
    expect(await screen.findByText('6th')).toBeTruthy();
    expect(pageRefresh().props.refreshing).toBe(false);
  });

  it('says why when it is refused, and Try again reads it again', async () => {
    rankingServer();
    transport.on('GET', rankingPath('PADEL'), () => errorResponse(503, 'service_unavailable'));
    await launchSignedIn();
    fireEvent.press(await screen.findByTestId('ranking-trophy'));
    await waitFor(() => expect(screen).toHavePathname('/rankings'));
    // Through the automatic retries the error model allows.
    await act(() => jest.advanceTimersByTimeAsync(30_000));

    const again = await screen.findByRole('button', { name: 'Try again' });
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.queryByTestId('place-card')).toBeNull();

    transport.on('GET', rankingPath('PADEL'), () => json(general('PADEL')));
    fireEvent.press(again);

    expect(await screen.findByText('7th')).toBeTruthy();
  });

  it('says it is offline, and reads the page once the connection is back', async () => {
    rankingServer();
    await launchSignedIn();
    await screen.findByTestId('ranking-trophy');
    act(() => onlineManager.setOnline(false));

    fireEvent.press(screen.getByTestId('ranking-trophy'));

    expect(
      await screen.findByText("You're offline. This will load as soon as you're back."),
    ).toBeTruthy();
    expect(rankingReads('PADEL')).toHaveLength(0);

    act(() => onlineManager.setOnline(true));

    expect(await screen.findByText('7th')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// General in pages, and the jump to his row (#776)
// ---------------------------------------------------------------------------

/*
 * Here Tomek is 212th of 480. **Each page holds a few rows rather than the server's 50**, so a test
 * renderer with no layout draws the whole list at once: the list asks for every page the same way
 * whatever a page holds.
 */

const rowsPath = (sport: Wire['Sport']) => `/api/v1/rankings/${sport}/general/rows`;

/** Somebody at a place in the long list — nobody in particular. */
const crowd = (place: number) => ranked(place, `player.${place}`, 3.9 - place / 200);
const placesFrom = (first: number, last: number) =>
  Array.from({ length: last - first + 1 }, (_unused, at) => first + at);
const crowdFrom = (first: number, last: number) => placesFrom(first, last).map(crowd);
const TOMEK_212 = { ...TOMEK, place: 212 };

function page(
  rows: readonly Wire['RankedRowSchema'][],
  previous: string | null,
  next: string | null,
): Wire['GeneralPageResponse'] {
  return { sport: 'PADEL', listed: 480, rows: [...rows], previous, next };
}

/**
 * The pages route, answering each query it is asked with its page, or with a refusal made afresh for
 * every read — anything else is refused as a page this server never wrote.
 */
function servePages(
  pages: Readonly<Record<string, Wire['GeneralPageResponse'] | (() => Response)>>,
) {
  transport.on('GET', rowsPath('PADEL'), (request) => {
    const answer = pages[request.path.split('?')[1] ?? ''];
    if (answer === undefined) return errorResponse(400, 'not_a_ranking_page');
    return typeof answer === 'function' ? answer() : json(answer);
  });
}

const AROUND_212 = page(
  [crowd(210), crowd(211), TOMEK_212, crowd(213), crowd(214)],
  'above-210',
  'below-214',
);

/** The main read with Tomek 212th of 480: the card, the podium, and the first page, 1–5. */
const LONG_LIST = () =>
  general('PADEL', {
    card: listedCard({ place: 212, of: 480 }),
    listed: 480,
    podium: crowdFrom(1, 3),
    rows: crowdFrom(1, 5),
    next: 'below-5',
  });

/** Tomek 212th: the main read's first page is 1–5, the pages after and around him as below. */
function longListServer(): RankingServer {
  const server = rankingServer({
    trophy: { sport: 'PADEL', general_place: 212, friends_place: null },
  });
  server.answer('PADEL', LONG_LIST());
  servePages({
    'after=below-5': page(crowdFrom(6, 10), 'above-6', 'below-10'),
    'around_me=true': AROUND_212,
    'before=above-210': page(crowdFrom(205, 209), 'above-205', 'below-209'),
    'after=below-214': page(crowdFrom(215, 219), 'above-215', 'below-219'),
  });
  return server;
}

const theList = () => screen.getByTestId('rankings-page');
const pageReads = () =>
  transport.requestsTo('GET', rowsPath('PADEL')).map((request) => request.path.split('?')[1]);
const drawnPlaces = () =>
  screen.getAllByTestId(/^ranked-place-/).map((node) => node.props.children as number);
const rowDrawn = (row: Wire['RankedRowSchema']) =>
  screen.findByTestId(`ranked-row-${row.player_id}`);
const jumpButton = (place: string) => screen.queryByRole('button', { name: `You · ${place}` });
/** The reader's finger on the list — what scrolling up or down from a jump begins with. */
const drag = () => fireEvent(theList(), 'scrollBeginDrag');

/**
 * **What the list reports as it settles** — the rows at least half on screen. The platform's list
 * measures that; a test renderer lays nothing out, so the test says it, as `endReached` is said.
 */
function reportOnScreen(...rows: readonly Wire['RankedRowSchema'][]) {
  fireEvent(theList(), 'viewableItemsChanged', {
    viewableItems: rows.map((row, index) => ({
      key: row.player_id,
      index,
      isViewable: true,
      item: { playerId: row.player_id, isYou: row.is_you },
    })),
    changed: [],
  });
}

describe('General in pages (#776)', () => {
  it('loads the next page as the list nears its end — asked once, each row once, none missing', async () => {
    longListServer();
    await openRankings();
    await rowDrawn(crowd(5));
    // The first page is the main read's own: nothing else is asked for until the end is near.
    expect(drawnPlaces()).toEqual(placesFrom(1, 5));
    expect(pageReads()).toEqual([]);

    fireEvent(theList(), 'endReached');
    // Reached again before the page has landed: the page on its way is the answer.
    fireEvent(theList(), 'endReached');

    await rowDrawn(crowd(10));
    expect(drawnPlaces()).toEqual(placesFrom(1, 10));
    expect(pageReads()).toEqual(['after=below-5']);
  });

  it('draws a row the next page brings back once, where it already stood', async () => {
    longListServer();
    // Player 5 dropped to 7th between the two reads, past the cursor: the next page brings them back.
    servePages({
      'after=below-5': page([crowd(6), { ...crowd(5), place: 7 }, crowd(8)], 'above-6', 'below-8'),
    });
    await openRankings();
    await rowDrawn(crowd(5));

    fireEvent(theList(), 'endReached');

    await rowDrawn(crowd(8));
    expect(drawnPlaces()).toEqual([1, 2, 3, 4, 5, 6, 8]);
    expect(screen.getAllByTestId(`ranked-row-${crowd(5).player_id}`)).toHaveLength(1);
  });

  it('asks for the page below once a pull that was on its way has landed', async () => {
    longListServer();
    await openRankings();
    await rowDrawn(crowd(5));
    let answer = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('GET', rankingPath('PADEL'), async () => {
      await held;
      return json(LONG_LIST());
    });
    fireEvent(pageRefresh(), 'refresh');
    await act(() => jest.advanceTimersByTimeAsync(100));

    // The end, reached while the list is read again: nothing asked yet…
    fireEvent(theList(), 'endReached');
    await act(() => jest.advanceTimersByTimeAsync(100));
    expect(pageReads()).toEqual([]);

    await act(async () => answer());

    // …and the page below once the read has landed, though the list never said the end again.
    await rowDrawn(crowd(10));
    expect(pageReads()).toEqual(['after=below-5']);
  });

  it('asks for nothing at the end of a list that is all on its first page', async () => {
    rankingServer();
    await openRankings();
    await rowDrawn(ZOFIA);

    fireEvent(theList(), 'endReached');
    fireEvent(theList(), 'startReached');
    await act(() => jest.advanceTimersByTimeAsync(1_000));

    expect(pageReads()).toEqual([]);
  });

  it('says why when the page below is refused, and Try again asks for it again', async () => {
    longListServer();
    servePages({ 'after=below-5': () => errorResponse(503, 'service_unavailable') });
    await openRankings();
    await rowDrawn(crowd(5));

    fireEvent(theList(), 'endReached');
    // Through the automatic retries the error model allows.
    await act(() => jest.advanceTimersByTimeAsync(30_000));

    const again = await screen.findByRole('button', { name: 'Try again' });
    expect(screen.getByRole('alert')).toBeTruthy();
    // The rows already drawn stay.
    expect(drawnPlaces()).toEqual(placesFrom(1, 5));

    servePages({ 'after=below-5': page(crowdFrom(6, 10), 'above-6', 'below-10') });
    fireEvent.press(again);

    await rowDrawn(crowd(10));
    expect(screen.queryByRole('alert')).toBeNull();
  });
});

describe('the You · 212th button (#776)', () => {
  let centring: jest.SpyInstance;
  beforeEach(() => {
    centring = jest.spyOn(FlatList.prototype, 'scrollToIndex');
  });
  afterEach(() => centring.mockRestore());

  it('shows while his row is off screen; a tap lands on the page around it, centred, and it hides once the row shows', async () => {
    longListServer();
    await openRankings();
    await rowDrawn(crowd(5));
    // Nothing floats before the list has said what is on screen.
    expect(jumpButton('212th')).toBeNull();

    reportOnScreen(crowd(1), crowd(2), crowd(3));
    const jump = screen.getByRole('button', { name: 'You · 212th' });
    expect(jump.props.accessibilityHint).toBe('Shows your row in the list');

    fireEvent.press(jump);

    await rowDrawn(TOMEK_212);
    expect(pageReads()).toEqual(['around_me=true']);
    // A new list: the page around him, his row in the middle of it…
    expect(drawnPlaces()).toEqual(placesFrom(210, 214));
    // …and in the middle of the screen.
    expect(centring).toHaveBeenLastCalledWith(
      expect.objectContaining({ index: 2, viewPosition: 0.5 }),
    );
    // The card and the podium stand at the top of the list, which is still to be read.
    expect(screen.queryByTestId('place-card')).toBeNull();
    expect(screen.queryByTestId('podium')).toBeNull();

    reportOnScreen(crowd(211), TOMEK_212, crowd(213));
    expect(jumpButton('212th')).toBeNull();

    // Scrolled away again, it comes back.
    reportOnScreen(crowd(213), crowd(214));
    expect(jumpButton('212th')).toBeTruthy();
  });

  it('loads the pages above and below his once it has jumped', async () => {
    longListServer();
    await openRankings();
    await rowDrawn(crowd(5));
    reportOnScreen(crowd(1));
    fireEvent.press(screen.getByRole('button', { name: 'You · 212th' }));
    await rowDrawn(TOMEK_212);
    // The new list starts at its top on the way to his row: nothing above is read for that.
    fireEvent(theList(), 'startReached');
    await act(() => jest.advanceTimersByTimeAsync(100));
    expect(pageReads()).toEqual(['around_me=true']);

    drag();
    fireEvent(theList(), 'startReached');
    await rowDrawn(crowd(205));
    fireEvent(theList(), 'endReached');
    await rowDrawn(crowd(219));

    expect(drawnPlaces()).toEqual(placesFrom(205, 219));
    expect(pageReads()).toEqual(['around_me=true', 'before=above-210', 'after=below-214']);
  });

  it('stands the card and the podium back above the rows once the pages above reach the top', async () => {
    // Tomek 7th of 13, the first page only three rows long, so his own is not on it.
    const server = rankingServer();
    server.answer('PADEL', general('PADEL', { rows: [INES, STAS, PIOTR], next: 'below-3' }));
    servePages({
      'around_me=true': page([KAROL, TOMEK, ZOFIA], 'above-6', null),
      'before=above-6': page([INES, STAS, PIOTR], null, 'below-3'),
    });
    await openRankings();
    await rowDrawn(PIOTR);
    reportOnScreen(INES, STAS);

    fireEvent.press(screen.getByRole('button', { name: 'You · 7th' }));
    await rowDrawn(TOMEK);
    expect(drawnPlaces()).toEqual([6, 7, 8]);
    expect(screen.queryByTestId('place-card')).toBeNull();

    drag();
    fireEvent(theList(), 'startReached');

    await rowDrawn(INES);
    expect(drawnPlaces()).toEqual([1, 2, 3, 6, 7, 8]);
    expect(screen.getByTestId('place-card')).toBeTruthy();
    expect(screen.getByTestId('podium')).toBeTruthy();
  });

  it('scrolls to his row where the list already draws it, reading nothing', async () => {
    rankingServer();
    await openRankings();
    await rowDrawn(TOMEK);
    reportOnScreen(INES, STAS, PIOTR);

    fireEvent.press(screen.getByRole('button', { name: 'You · 7th' }));

    expect(centring).toHaveBeenCalledWith({ index: 6, viewPosition: 0.5, animated: true });
    expect(pageReads()).toEqual([]);
  });

  it('is not shown when he is not listed', async () => {
    const server = rankingServer();
    server.answer('PADEL', general('PADEL', { card: notListed('NEEDS_RESULTS', { results: 2 }) }));
    await openRankings();
    await rowDrawn(INES);

    reportOnScreen(INES, STAS, PIOTR);

    expect(screen.queryByRole('button', { name: /^You · / })).toBeNull();
  });

  it('says why where it stood when the jump is refused, and Try again jumps', async () => {
    longListServer();
    servePages({ 'around_me=true': () => errorResponse(503, 'service_unavailable') });
    await openRankings();
    await rowDrawn(crowd(5));
    reportOnScreen(crowd(1));

    fireEvent.press(screen.getByRole('button', { name: 'You · 212th' }));
    await act(() => jest.advanceTimersByTimeAsync(30_000));

    const again = await screen.findByRole('button', { name: 'Try again' });
    // The list stays where it was.
    expect(drawnPlaces()).toEqual(placesFrom(1, 5));
    expect(jumpButton('212th')).toBeNull();

    servePages({ 'around_me=true': AROUND_212 });
    fireEvent.press(again);

    await rowDrawn(TOMEK_212);
    expect(drawnPlaces()).toEqual(placesFrom(210, 214));
  });

  it('reads the page around him again on a pull, with the card', async () => {
    longListServer();
    await openRankings();
    await rowDrawn(crowd(5));
    reportOnScreen(crowd(1));
    fireEvent.press(screen.getByRole('button', { name: 'You · 212th' }));
    await rowDrawn(TOMEK_212);

    await act(async () => {
      fireEvent(pageRefresh(), 'refresh');
    });

    await waitFor(() => expect(pageReads()).toEqual(['around_me=true', 'around_me=true']));
    await waitFor(() => expect(rankingReads('PADEL')).toHaveLength(2));
    expect(drawnPlaces()).toEqual(placesFrom(210, 214));
    expect(pageRefresh().props.refreshing).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// General | Friends, and the view the phone remembers (#777)
// ---------------------------------------------------------------------------

const viewSegment = (view: 'General' | 'Friends', selected?: boolean) =>
  screen.getByRole('button', { name: view, ...(selected === undefined ? {} : { selected }) });

/** Rankings, opened on Friends — the view the phone remembers from an earlier visit. */
async function openFriends(sport: Wire['Sport'] = 'PADEL') {
  await savePhonePreference(GATE_USER.id, 'rankingView', 'FRIENDS');
  await openRankings(sport);
}

describe('the General | Friends switch (#777)', () => {
  it('opens on General the first time; Friends reads the page again for the view, and is remembered', async () => {
    rankingServer();
    await openRankings();
    await rowDrawn(KAROL);
    expect(viewSegment('General', true)).toBeTruthy();
    expect(viewSegment('Friends', false)).toBeTruthy();

    fireEvent.press(viewSegment('Friends'));

    // Everything below the switch is the view's own: his Friends place, its line, its table.
    // (The choice reaches the page on the cache's next tick, so wait for the place, not the card.)
    await screen.findByText('4th');
    const card = within(screen.getByTestId('place-card'));
    expect(card.getByText('4th')).toBeTruthy();
    expect(card.getByText('of 9')).toBeTruthy();
    expect(said(screen.getByTestId('gap-line'))).toBe(
      '0,09 behind Ola · about 2 wins close it · Kasia is 0,11 behind you',
    );
    expect(viewReads('PADEL', 'FRIENDS')).toHaveLength(1);
    expect(viewSegment('Friends', true)).toBeTruthy();
    expect(screen.queryByTestId(`ranked-row-${KAROL.player_id}`)).toBeNull();
    expect(within(screen.getByTestId('podium-first')).getByText('Ania')).toBeTruthy();
    // Kept on the phone, for this account.
    await waitFor(async () =>
      expect(await readPhonePreference(GATE_USER.id, 'rankingView')).toBe('FRIENDS'),
    );

    fireEvent.press(viewSegment('General'));

    expect(await screen.findByText('7th')).toBeTruthy();
    expect(await rowDrawn(KAROL)).toBeTruthy();
    // Read again for the view, however lately it was read (the screens §3).
    await waitFor(() => expect(viewReads('PADEL', 'GENERAL')).toHaveLength(2));
    await waitFor(async () =>
      expect(await readPhonePreference(GATE_USER.id, 'rankingView')).toBe('GENERAL'),
    );
  });

  it('a sport switched on Friends is read in Friends', async () => {
    rankingServer();
    await openFriends();
    await screen.findByText('4th');

    unfoldThePill('Padel');
    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Tennis' }),
    );

    await waitFor(() => expect(viewReads('TENNIS', 'FRIENDS')).toHaveLength(1));
    expect(viewReads('TENNIS', 'GENERAL')).toHaveLength(0);
    expect(await screen.findByText('None of your friends is ranked in tennis yet')).toBeTruthy();
  });

  it('opens next time on the view last looked at, reading nothing for the other', async () => {
    rankingServer();
    await openFriends();

    expect(await screen.findByText('4th')).toBeTruthy();
    expect(viewSegment('Friends', true)).toBeTruthy();
    expect(viewReads('PADEL', 'FRIENDS')).toHaveLength(1);
    expect(viewReads('PADEL', 'GENERAL')).toHaveLength(0);
  });
});

describe('Home’s trophy follows the view (#777)', () => {
  it('reads the Friends place once Friends was last looked at, and opens on Friends', async () => {
    rankingServer();
    await openRankings();
    await screen.findByText('7th');
    fireEvent.press(viewSegment('Friends'));
    await screen.findByText('4th');

    fireEvent.press(screen.getByLabelText('Back to Home'));
    await waitFor(() => expect(screen).toHavePathname('/'));

    await waitFor(() => expect(within(trophy()).getByText('#4')).toBeTruthy());
    expect(trophy().props.accessibilityLabel).toBe('Rankings, 4th among your friends in padel');

    fireEvent.press(trophy());

    await waitFor(() => expect(screen).toHavePathname('/rankings'));
    expect(await screen.findByText('4th')).toBeTruthy();
    expect(viewSegment('Friends', true)).toBeTruthy();
  });

  it('reads the Friends place from a launch, the view kept on the phone', async () => {
    rankingServer();
    await savePhonePreference(GATE_USER.id, 'rankingView', 'FRIENDS');
    await launchSignedIn();

    await waitFor(() => expect(within(trophy()).getByText('#4')).toBeTruthy());
    expect(within(trophy()).queryByText('#7')).toBeNull();
  });

  it('draws no number with no Friends place, and still opens Rankings on Friends', async () => {
    rankingServer({ trophy: { sport: 'PADEL', general_place: 7, friends_place: null } });
    await savePhonePreference(GATE_USER.id, 'rankingView', 'FRIENDS');
    await launchSignedIn();

    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/home').length).toBe(1));
    // General's #7 is not the Friends place: nothing rather than the other view's number.
    expect(within(trophy()).queryByText(/^#/)).toBeNull();
    expect(trophy().props.accessibilityLabel).toBe('Rankings');

    fireEvent.press(trophy());

    await waitFor(() => expect(viewReads('PADEL', 'FRIENDS')).toHaveLength(1));
    expect(viewReads('PADEL', 'GENERAL')).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// The Friends view (#777; the screens §4.6)
// ---------------------------------------------------------------------------

const OGRODY: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000777',
  kind: 'OFFICIAL',
  name: 'Ogrody open play',
  monogram: { letters: 'Oo', colour: 2 },
  sports: ['PADEL'],
  member_count: 8,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Ogrody 33' },
};

describe('the Friends view (#777)', () => {
  it('listed: the whole table, its podium, rows and chips as in General, his own row You', async () => {
    rankingServer();
    await openFriends();
    await rowDrawn(KASIA);

    expect(drawnPlaces()).toEqual(placesFrom(1, 9));
    expect(within(screen.getByTestId('podium-second')).getByText('Bartek')).toBeTruthy();
    expect(within(screen.getByTestId('podium-third')).getByText('Ola')).toBeTruthy();
    expect(within(rowOf(TOMEK_AMONG_FRIENDS)).getByText('You')).toBeTruthy();
    expect(within(rowOf(ANIA)).getByTestId('rank-chip-UP', HIDDEN_TOO)).toBeTruthy();
    // Whole, never paged: neither end asks for anything.
    fireEvent(theList(), 'endReached');
    fireEvent(theList(), 'startReached');
    await act(() => jest.advanceTimersByTimeAsync(1_000));
    expect(transport.requestsTo('GET', rowsPath('PADEL'))).toHaveLength(0);
  });

  describe('the You · 4th button', () => {
    let centring: jest.SpyInstance;
    beforeEach(() => {
      centring = jest.spyOn(FlatList.prototype, 'scrollToIndex');
    });
    afterEach(() => centring.mockRestore());

    it('shows while his row is off screen, and a tap scrolls to it, reading nothing', async () => {
      rankingServer();
      await openFriends();
      await rowDrawn(KASIA);

      reportOnScreen(ANIA, BARTEK);
      fireEvent.press(screen.getByRole('button', { name: 'You · 4th' }));

      expect(centring).toHaveBeenCalledWith({ index: 3, viewPosition: 0.5, animated: true });
      expect(transport.requestsTo('GET', rowsPath('PADEL'))).toHaveLength(0);
      expect(viewReads('PADEL', 'FRIENDS')).toHaveLength(1);

      reportOnScreen(OLA, TOMEK_AMONG_FRIENDS, KASIA);
      expect(jumpButton('4th')).toBeNull();
    });
  });

  it.each<[string, Wire['RankingResponse'], string]>([
    [
      'just you so far',
      friends('PADEL', {
        card: notListed('JUST_YOU', { results_to_enter: 1 }),
        listed: 1,
        podium: [],
        rows: [],
      }),
      'Just you so far',
    ],
    [
      'none of his friends ranked',
      NO_FRIEND('PADEL'),
      'None of your friends is ranked in padel yet',
    ],
  ])('%s: the line, and nothing below; Add friends opens the sheet', async (_case, read, line) => {
    const server = rankingServer();
    server.answerFriends('PADEL', read);
    await openFriends();

    expect(said(await screen.findByTestId('friends-card-line'))).toBe(line);
    expect(screen.queryByTestId('place-card')).toBeNull();
    expect(screen.queryByTestId('podium')).toBeNull();
    expect(screen.queryByTestId('nobody-ranked')).toBeNull();
    expect(listedRows()).toHaveLength(0);
    expect(screen.queryByRole('button', { name: /^You · / })).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: 'Add friends' }));

    expect(await screen.findByRole('header', { name: 'Add friends' })).toBeTruthy();
  });

  it('Add friends opens the Add friends sheet: your groups, and your friend link', async () => {
    const server = rankingServer();
    server.answerFriends('PADEL', NO_FRIEND('PADEL'));
    stubMyGroups(transport, [OGRODY]);
    transport.on('GET', FRIENDS_GROUPS_PATH, () =>
      json<Wire['GroupsToAddFromResponse']>({
        groups: [{ group_id: OGRODY.id, name: OGRODY.name, member_count: 8, to_add: 2 }],
      }),
    );
    await openFriends();

    fireEvent.press(await screen.findByRole('button', { name: 'Add friends' }));

    expect(await screen.findByRole('header', { name: 'Add friends' })).toBeTruthy();
    expect(await screen.findByText('8 members · 2 to add')).toBeTruthy();
    expect(await screen.findByText('raketa.app/f/tk4m9q2z')).toBeTruthy();
    // A group opens its Members, the sheet closing first.
    fireEvent.press(screen.getByTestId(`add-from-${OGRODY.id}`));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${OGRODY.id}/members`));
  });

  it.each<[string, Wire['PlaceCardSchema'], string]>([
    [
      'not ranked yet',
      notListed('NEEDS_RESULTS', { results: 0, results_to_enter: 1 }),
      'Not ranked in padel yet — your first confirmed competitive game puts you on the list',
    ],
    [
      'off the list',
      notListed('OFF_THE_LIST', { results: 12, results_to_enter: 1 }),
      'Off the list — no competitive padel game in 90 days. Your next one puts you back.',
    ],
  ])('%s: his card above his friends’ podium and table', async (_case, card, line) => {
    const server = rankingServer();
    server.answerFriends(
      'PADEL',
      friends('PADEL', { card, listed: 8, rows: ONLY_FRIENDS, podium: [ANIA, BARTEK, OLA] }),
    );
    await openFriends();

    expect(said(await screen.findByTestId('not-listed-line'))).toBe(line);
    expect(screen.queryByTestId('place-card')).toBeNull();
    expect(screen.getByTestId('podium')).toBeTruthy();
    await rowDrawn(KASIA);
    expect(listedRows()).toHaveLength(8);
    expect(screen.queryByRole('button', { name: /^You · / })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Add friends' })).toBeNull();
  });

  it('no level: one competitive game after a level, with Get your squash level, above the table', async () => {
    const server = rankingServer();
    const squashFriends = [friend(1, 'Ania', 2.9), friend(2, 'Ola', 2.5)];
    server.answerFriends(
      'SQUASH',
      friends('SQUASH', {
        card: notListed('NO_LEVEL', { results_to_enter: 1 }),
        listed: 2,
        podium: [],
        rows: squashFriends,
      }),
    );
    await openFriends();
    await screen.findByText('4th');

    unfoldThePill('Padel');
    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Squash' }),
    );

    expect(said(await screen.findByTestId('not-listed-line'))).toBe(
      'No squash level yet — get one, then one competitive game puts you on the list',
    );
    expect(screen.getByRole('button', { name: 'Get your squash level' })).toBeTruthy();
    expect(await screen.findAllByTestId(/^ranked-row-/)).toHaveLength(2);
  });

  it('reads Friends again on a pull', async () => {
    const server = rankingServer();
    await openFriends();
    await screen.findByText('4th');
    server.answerFriends('PADEL', friends('PADEL', { card: { ...FRIENDS_CARD, place: 3 } }));

    await act(async () => {
      fireEvent(pageRefresh(), 'refresh');
    });

    await waitFor(() => expect(viewReads('PADEL', 'FRIENDS')).toHaveLength(2));
    expect(await screen.findByText('3rd')).toBeTruthy();
    expect(viewReads('PADEL', 'GENERAL')).toHaveLength(0);
  });
});
