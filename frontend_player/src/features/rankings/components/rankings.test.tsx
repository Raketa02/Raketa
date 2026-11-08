/**
 * **The trophy on Home and the General page, walked through the real route tree**
 * ([#775](https://github.com/Raketa02/Raketa/issues/775), PRD #766;
 * [ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md); the rankings
 * screens §1–§6), with only `fetch` faked.
 *
 * Tomek is 7th of 13 in padel at 2,71: Karol just above at 2,75, Zofia just below at 2,69, Inés at the
 * top at 3,40. Places 4 and 5 are rows he can't see, so his list skips them. He has no squash level,
 * and nobody is ranked in badminton.
 *
 * Every assertion is about what the player can see, or what left the device.
 */

import { onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { RefreshControl, StyleSheet } from 'react-native';

import { OWN_RECORD_TITLE, RECORD_TITLE } from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { savePhonePreference } from '@/shared/lib/preferences';
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
const KAROL = ranked(6, 'Karol', 2.75);
const TOMEK = ranked(7, GATE_USER.nickname ?? 'tomek.k', 2.71, {
  player_id: GATE_USER.id,
  form: ['WIN', 'LOSS', 'WIN'],
  chip: { kind: 'UP', places: 1 },
  is_you: true,
});
const ZOFIA = ranked(8, 'Zofia', 2.69, { chip: { kind: 'DOWN', places: 2 } });
const PADEL_ROWS = [INES, STAS, PIOTR, KAROL, TOMEK, ZOFIA];

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
// The server
// ---------------------------------------------------------------------------

let transport: Transport;

interface RankingServer {
  /** Answer one sport's General read with this, from now on. */
  readonly answer: (sport: Wire['Sport'], read: Wire['RankingResponse']) => void;
}

/**
 * **Tomek, set up long ago and rated in padel and tennis**, with Home's trophy as given, every sport's
 * General as above, and the records a row opens.
 */
function rankingServer({
  trophy = { sport: 'PADEL', general_place: 7, friends_place: null },
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

  const reads = new Map<Wire['Sport'], Wire['RankingResponse']>([
    ['PADEL', general('PADEL')],
    ['TENNIS', general('TENNIS', { rows: [], podium: [], listed: 0 })],
    ['SQUASH', SQUASH()],
    ['BADMINTON', BADMINTON()],
  ]);
  for (const sport of ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'] as const) {
    transport.on('GET', rankingPath(sport), () => json(reads.get(sport)!));
  }

  for (const row of PADEL_ROWS.filter((one) => !one.is_you)) {
    transport.on('GET', recordPath(row.player_id), () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: 'NONE',
        can_add_friend: true,
        nickname: row.nickname,
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: row.level, band: 'Established' }],
        reliability: servedReliability({ player_score: 96, is_new: false }),
      }),
    );
  }

  return { answer: (sport, read) => reads.set(sport, read) };
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
  it('reads #7 left of the bell, and opens Rankings on its sport with the Home tab lit', async () => {
    rankingServer({ trophy: { sport: 'TENNIS', general_place: 7, friends_place: null } });
    await launchSignedIn();

    await waitFor(() => expect(within(trophy()).getByText('#7')).toBeTruthy());
    expect(trophy().props.accessibilityLabel).toBe('Rankings, 7th in tennis');
    // The bell keeps the corner, beside it.
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

  it('hidden from General: the place, and Hidden from General where the gap line was', async () => {
    const server = rankingServer();
    server.answer(
      'PADEL',
      general('PADEL', { card: listedCard({ state: 'HIDDEN', gap_line: null }) }),
    );
    await openRankings();

    expect(await screen.findByText('7th')).toBeTruthy();
    expect(screen.getByText('Hidden from General')).toBeTruthy();
    expect(screen.queryByTestId('gap-line')).toBeNull();
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
    expect(screen.getByTestId('ranking-list')).toBeTruthy();
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

  it('labels each step with its true place — with second hidden, 1, 3 and 4', async () => {
    const server = rankingServer();
    const fourth = ranked(4, 'Marek', 2.92);
    server.answer('PADEL', general('PADEL', { podium: [INES, PIOTR, fourth] }));
    await openRankings();

    const podium = await screen.findByTestId('podium');
    expect(within(screen.getByTestId('podium-first')).getByText('1')).toBeTruthy();
    expect(within(screen.getByTestId('podium-second')).getByText('3')).toBeTruthy();
    expect(within(screen.getByTestId('podium-third')).getByText('4')).toBeTruthy();
    expect(podium).toBeTruthy();
  });

  it('is not drawn with fewer than three rows: the list shows alone', async () => {
    const server = rankingServer();
    server.answer('PADEL', general('PADEL', { podium: [], rows: [INES, TOMEK], listed: 2 }));
    await openRankings();

    expect(await screen.findByTestId('ranking-list')).toBeTruthy();
    expect(screen.queryByTestId('podium')).toBeNull();
  });
});

describe('the rows', () => {
  it('draw each place — coral for 1–3, grey after, skipping the rows he can’t see', async () => {
    rankingServer();
    await openRankings();
    await screen.findByTestId('ranking-list');

    const places = within(screen.getByTestId('ranking-list'))
      .getAllByTestId(/^ranked-place-/)
      .map((node) => [node.props.children as number, StyleSheet.flatten(node.props.style).color]);
    expect(places).toEqual([
      [1, theme.color.coralInk],
      [2, theme.color.coralInk],
      [3, theme.color.coralInk],
      [6, theme.color.muted],
      [7, theme.color.muted],
      [8, theme.color.muted],
    ]);
  });

  it('draw the form as the record’s squares, oldest first and never padded', async () => {
    rankingServer();
    await openRankings();
    await screen.findByTestId('ranking-list');

    expect(formOf(INES)).toEqual(['WIN', 'WIN', 'LOSS', 'WIN', 'WIN']);
    expect(formOf(TOMEK)).toEqual(['WIN', 'LOSS', 'WIN']);
  });

  it('draw every chip: up and down with their counts, the same, and New', async () => {
    rankingServer();
    await openRankings();
    await screen.findByTestId('ranking-list');

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
    await screen.findByTestId('ranking-list');

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
    expect(screen.queryByTestId('ranking-list')).toBeNull();
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

  it('opens the reader’s own record from their own row', async () => {
    rankingServer();
    await openRankings();

    fireEvent.press(await screen.findByTestId(`ranked-row-${TOMEK.player_id}`));

    expect(await screen.findByText(OWN_RECORD_TITLE)).toBeTruthy();
    expect(transport.requestsTo('GET', recordPath(TOMEK.player_id))).toHaveLength(0);
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
    transport.on('GET', rankingPath('PADEL'), () => errorResponse(503, 'block_state_unavailable'));
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
