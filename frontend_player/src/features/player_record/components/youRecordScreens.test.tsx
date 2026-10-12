/**
 * **The two read-only screens on the You tab, walked through the real route tree** — the
 * Skill passport and Player reliability
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2–§3).
 *
 * The passport is the result card once per rating and the reliability screen is the record
 * card under a ring, and both of those drawings have suites of their own. What is proved here
 * is what the two screens add: a card **per** rating with its status chip, no ceiling tick
 * where none was served, the record's blocks under each card from that sport's read, *Add a
 * sport* drawn and inert, the ladder printing only the edges it was sent; the figure in points
 * with the band's word, the four counts, and the one sentence a new player is told (#660); the
 * filter's switch writing what is tapped and drawing what the re-read says is saved, its *hides*
 * line, and the hidden player's sentence (#662).
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { ratingStatusLabel } from '@/features/onboarding/types';
import { formatRange } from '@/shared/formatting/ratingFormat';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel } from '@/shared/ui';
import {
  OWN_RECORD_PATH,
  OWN_RECORD_SERVED,
  SPORTS_SERVED,
  launchSignedIn,
  stubGate,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  FILTER_OFF,
  HIDDEN_BY_A_HIGH_FILTER,
  MARTA_FILTER,
  SERGIO_RELIABILITY,
  servedReliability,
} from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import {
  COUNTED_BLOCK,
  FULL_RECORD,
  LAST_FIVE_BLOCK,
  OWN_RECORD_TITLE,
  PLAYER_SCORE_BLOCK,
  SPORTSMANSHIP_LABEL,
  VARIETY_LABEL,
  opinionFigure,
  recordBlocksLabel,
  recordCardLabel,
} from './recordPresentation';
import {
  ADD_A_SPORT,
  FILTER_LABEL,
  FILTER_POSITION_SPOKEN,
  HOW_OTHERS_SEE_YOU_LINE,
  HOW_OTHERS_SEE_YOU_TITLE,
  NEW_PLAYER_NOTE,
  OUT_OF_100,
  PLAYER_RELIABILITY_TITLE,
  SKILL_PASSPORT_TITLE,
  THE_LADDER,
  backWithEveryoneLine,
  hidesLine,
  ladderRung,
  passportLine,
  rateSportChip,
  reliabilityLine,
  scoreRingLabel,
} from './youRecordPresentation';

function rating(
  sport: Wire['Sport'],
  over: Partial<Wire['RatingResponse']> = {},
): Wire['RatingResponse'] {
  return {
    sport,
    mu: 2.71,
    sigma: 0.62,
    confidence: 28,
    range: { low: 2.09, high: 3.33 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
    ...over,
  };
}

/** Padel calibrating at 61 %, tennis still an estimate — two chips, two cards. */
const PADEL = rating('PADEL', { mu: 2.71, confidence: 61, status: 'calibrating' });
const TENNIS = rating('TENNIS', {
  mu: 3.1,
  confidence: 27,
  range: { low: 2.22, high: 3.98 },
  band: { name: 'Developing', lower: 1.6, upper: 2.6 },
});

const SQUASH_RUN = '7a8b9c0d-1e2f-4a3b-8c4d-5e6f7a8b9c0d';

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL, TENNIS], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const PASSPORT_LINE = passportLine([
  { sport: 'padel', level: 2.71 },
  { sport: 'tennis', level: 3.1 },
]);

async function onYou() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  await screen.findByLabelText(doorRowLabel(SKILL_PASSPORT_TITLE, PASSPORT_LINE));
}

// ---------------------------------------------------------------------------
// The Skill passport
// ---------------------------------------------------------------------------

describe('the Skill passport', () => {
  async function openThePassport() {
    await onYou();
    fireEvent.press(screen.getByLabelText(doorRowLabel(SKILL_PASSPORT_TITLE, PASSPORT_LINE)));
    await screen.findByRole('header', { name: SKILL_PASSPORT_TITLE });
    await screen.findByText(THE_LADDER);
  }

  it('draws the result card once per rating, with the sport and a status chip across its top', async () => {
    await openThePassport();

    // Two cards: two levels, two status rows.
    expect(screen.getByText('2,71')).toBeTruthy();
    expect(screen.getByText('3,10')).toBeTruthy();
    expect(screen.getAllByText('Rating status')).toHaveLength(2);
    // The chip and the row both say the status, so each word is drawn twice per card.
    expect(screen.getAllByText(ratingStatusLabel('calibrating'))).toHaveLength(2);
    expect(screen.getAllByText(ratingStatusLabel('initial_estimate'))).toHaveLength(2);
    expect(screen.getByText('Padel')).toBeTruthy();
    expect(screen.getByText('Tennis')).toBeTruthy();
    // The run's own row is not the passport's.
    expect(screen.queryByText('Questions asked')).toBeNull();
  });

  it('draws no ceiling tick, because the ratings read serves no ceiling', async () => {
    await openThePassport();

    // The ring's name states the one number it has; a served ceiling would put a second in it.
    expect(screen.getByLabelText('Confidence 61%')).toBeTruthy();
    expect(screen.getByLabelText('Confidence 27%')).toBeTruthy();
    expect(screen.queryByLabelText(/a questionnaire can prove/)).toBeNull();
  });

  it('draws the record’s three blocks under each card, from that sport’s read', async () => {
    await openThePassport();

    // Padel's read holds a run and a count; the whole person's score is on every card.
    await waitFor(() =>
      expect(transport.requestsTo('GET', OWN_RECORD_PATH).map((r) => r.path)).toEqual(
        expect.arrayContaining([
          `${OWN_RECORD_PATH}?sport=PADEL`,
          `${OWN_RECORD_PATH}?sport=TENNIS`,
        ]),
      ),
    );
    expect(
      await screen.findByLabelText(
        recordBlocksLabel({
          reliability: { playerScore: 75, band: 'HIGH', isNew: false },
          lastFive: ['WIN', 'LOSS', 'WIN', 'WIN', 'LOSS'],
          countedGames: 9,
        }),
      ),
    ).toBeTruthy();
    expect(screen.getAllByText(PLAYER_SCORE_BLOCK).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(LAST_FIVE_BLOCK).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(COUNTED_BLOCK).length).toBeGreaterThanOrEqual(1);
  });

  it('offers each unrated sport as a chip, and a chip begins that sport’s pass', async () => {
    await openThePassport();

    expect(await screen.findByText(ADD_A_SPORT)).toBeTruthy();
    const squash = screen.getByLabelText(rateSportChip('squash'));
    expect(screen.getByLabelText(rateSportChip('badminton'))).toBeTruthy();
    expect(screen.queryByLabelText(rateSportChip('padel'))).toBeNull();

    transport.on('POST', '/api/v1/assessments', () =>
      json<Wire['AssessmentStepResponse']>(
        {
          assessment_id: SQUASH_RUN,
          status: 'in_progress',
          questions_asked: 0,
          transcript: [],
          question: {
            id: 'q-played',
            category: 'Recent activity',
            tier: null,
            situation: 'Before anything else',
            text: 'Have you played squash before?',
            qualifier: 'Any level counts',
            options: [{ id: 'never', text: 'Never played' }],
          },
        },
        201,
      ),
    );
    fireEvent.press(squash);

    // The second door into the onboarding pass (ADR-0179 §3): one start naming the sport,
    // and the questionnaire opens at its first question — never the picker.
    await waitFor(() => expect(screen).toHavePathname(`/question/${SQUASH_RUN}`));
    expect(transport.requestsTo('POST', '/api/v1/assessments').map((r) => r.body)).toEqual([
      { sport: 'SQUASH' },
    ]);
    expect(await screen.findByText('Have you played squash before?')).toBeTruthy();
  });

  it('marks the player’s rungs on the ladder, and prints an edge only where a rating served one', async () => {
    await openThePassport();

    expect(screen.getByText(ladderRung('Established', ['padel']))).toBeTruthy();
    expect(screen.getByText(ladderRung('Developing', ['tennis']))).toBeTruthy();
    // The two rungs the player is not on carry no *you* — found by the rung's spoken name,
    // since the bars above print every band's bare name too.
    expect(screen.getByLabelText(/^New\. You are starting out/)).toBeTruthy();
    expect(screen.getByLabelText(/^Advanced\. You compete/)).toBeTruthy();
    // The served edges, in the response's own numbers — and none invented for the other two.
    expect(screen.getByText(formatRange({ low: 2.7, high: 3.8 }))).toBeTruthy();
    expect(screen.getByText(formatRange({ low: 1.6, high: 2.6 }))).toBeTruthy();
    expect(screen.queryByText(formatRange({ low: 1, high: 1.5 }))).toBeNull();
    expect(screen.queryByText(formatRange({ low: 3.9, high: 5 }))).toBeNull();
  });

  it('draws no Add a sport card for a player rated in every sport', async () => {
    stubGate(transport, {
      ratings: [PADEL, TENNIS, rating('SQUASH'), rating('BADMINTON')],
      hasPlayerProfile: true,
    });
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));
    fireEvent.press(await screen.findByLabelText(SKILL_PASSPORT_TITLE, { exact: false }));
    await screen.findByText(THE_LADDER);

    expect(screen.queryByText(ADD_A_SPORT)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Player reliability
// ---------------------------------------------------------------------------

describe('Player reliability', () => {
  /** The served record is Sergio's six months: 75 · High. */
  const RELIABILITY_LINE = reliabilityLine({ playerScore: 75, band: 'HIGH', isNew: false });

  async function openReliability(line: string = RELIABILITY_LINE) {
    await onYou();
    fireEvent.press(await screen.findByLabelText(doorRowLabel(PLAYER_RELIABILITY_TITLE, line)));
    await screen.findByRole('header', { name: PLAYER_RELIABILITY_TITLE });
  }

  /**
   * **Sergio reads 75 · High, and the four counts** (#660) — the figure in the ring, the band's
   * word beside it, *Out of 100* under that, then *Shows up*, *Keeps plans*, *Being late* and
   * *Results left in dispute* as the record serves them, and the two rows under them.
   */
  it('draws the points with the band’s word, then the four counts and the two rows under them', async () => {
    expect(RELIABILITY_LINE).toBe('75 · High');
    await openReliability();

    expect(await screen.findByLabelText(scoreRingLabel(75))).toBeTruthy();
    expect(screen.getByText('High reliability')).toBeTruthy();
    expect(screen.getByText(OUT_OF_100)).toBeTruthy();
    expect(screen.getByText('Shows up')).toBeTruthy();
    expect(screen.getByText('turned up 12 of 13')).toBeTruthy();
    expect(screen.getByText('Keeps plans')).toBeTruthy();
    expect(screen.getByText('kept 13 of 14')).toBeTruthy();
    expect(screen.getByText('Being late')).toBeTruthy();
    expect(screen.getByText('late 1 time')).toBeTruthy();
    expect(screen.getByText('Results left in dispute')).toBeTruthy();
    // Every count's value, as the card speaks it — *Results left in dispute, 0* included.
    expect(
      screen.getByLabelText(
        recordCardLabel({
          counts: { turnedUp: 12, turnedUpOf: 13, late: 1, kept: 13, keptOf: 14, leftInDispute: 0 },
          variety: { distinctOpponents: 14, timesOnCourt: 20 },
          opinion: { average: 4.3, raters: 12 },
        }),
      ),
    ).toBeTruthy();
    expect(screen.getByText(VARIETY_LABEL)).toBeTruthy();
    expect(screen.getByText(SPORTSMANSHIP_LABEL)).toBeTruthy();
    expect(screen.getByText(opinionFigure({ average: 4.3, raters: 12 }))).toBeTruthy();
    // No meter and no retired word: the one progress drawing is the ring, and neither the
    // ladder's three words nor the sportsmanship band's three are anywhere on the screen.
    expect(screen.getAllByRole('progressbar')).toEqual([screen.getByLabelText(scoreRingLabel(75))]);
    expect(screen.queryByText(/^(Reliable|Holding|Under the bar)$/)).toBeNull();
    expect(screen.queryByText(/^(Good|Mixed|Poor)$/)).toBeNull();
    // Sergio is not new, so nobody tells him where the figure starts.
    expect(screen.queryByText(NEW_PLAYER_NOTE)).toBeNull();
  });

  /**
   * **Nerea reads 100 · New** — on the You row and on the screen — and the one sentence a new
   * player is told, which speaks of games and never of plans. Her counts are drawn as served:
   * nothing has fallen due for her yet.
   */
  it('reads 100 · New for a new player, with the sentence that says what that is', async () => {
    stubOwnRecord(transport, { ...OWN_RECORD_SERVED, reliability: servedReliability() });
    await openReliability(reliabilityLine({ playerScore: 100, band: 'VERY_HIGH', isNew: true }));

    expect(await screen.findByLabelText(scoreRingLabel(100))).toBeTruthy();
    expect(screen.getByText('New')).toBeTruthy();
    expect(screen.queryByText('Very high reliability')).toBeNull();
    expect(screen.getByText(NEW_PLAYER_NOTE)).toBeTruthy();
    expect(screen.getByText('turned up 0 of 0')).toBeTruthy();
  });

  /** The word is the server's band — a 49 served Low reads *Low reliability*. */
  it('draws the band the server served', async () => {
    stubOwnRecord(transport, {
      ...OWN_RECORD_SERVED,
      reliability: { ...SERGIO_RELIABILITY, player_score: 49, band: 'LOW', turned_up: 10 },
    });
    await openReliability(reliabilityLine({ playerScore: 49, band: 'LOW', isNew: false }));

    expect(await screen.findByText('Low reliability')).toBeTruthy();
    expect(screen.getByText('turned up 10 of 13')).toBeTruthy();
  });

  /**
   * **A player nobody has rated draws no sportsmanship row, as before** — its own absence,
   * asking its own question: the rows above it are still drawn, and nothing is drawn at nought.
   */
  it('draws no sportsmanship row for a player nobody has rated', async () => {
    const { sportsmanship: _nobody, ...unrated } = OWN_RECORD_SERVED;
    stubOwnRecord(transport, unrated);
    await openReliability();

    expect(await screen.findByText('Shows up')).toBeTruthy();
    expect(screen.getByText(VARIETY_LABEL)).toBeTruthy();
    expect(screen.queryByText(SPORTSMANSHIP_LABEL)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The filter
// ---------------------------------------------------------------------------

/**
 * **Marta switches it on, and both sides understand** (#662, ADR-0195 §6). The switch writes the
 * position tapped and draws what the re-read says is saved; the *hides* line shows while a filter
 * is on; and a hidden player reads the sentence that names nobody and gives the figure.
 */
describe('the reliability filter', () => {
  const FILTER_PATH = '/api/v1/players/me/reliability-filter';
  const RELIABILITY_LINE = reliabilityLine({ playerScore: 75, band: 'HIGH', isNew: false });

  /** The own record, answered live: a save moves what the next read says. */
  function serveOwnRecord(filter: Wire['ReliabilityFilterSchema']) {
    const served = { ...OWN_RECORD_SERVED, reliability: { ...SERGIO_RELIABILITY, filter } };
    transport.on('GET', OWN_RECORD_PATH, () => json(served));
  }

  async function openReliability(line: string = RELIABILITY_LINE) {
    await onYou();
    fireEvent.press(await screen.findByLabelText(doorRowLabel(PLAYER_RELIABILITY_TITLE, line)));
    await screen.findByRole('header', { name: PLAYER_RELIABILITY_TITLE });
    await screen.findByText(FILTER_LABEL);
  }

  function segment(position: keyof typeof FILTER_POSITION_SPOKEN) {
    return screen.getByRole('button', { name: FILTER_POSITION_SPOKEN[position] });
  }

  /** The one raised segment, as a listener is told it: the three asked by name and state. */
  function expectSaved(saved: keyof typeof FILTER_POSITION_SPOKEN) {
    for (const position of ['OFF', 'MEDIUM', 'HIGH'] as const) {
      expect(
        screen.getByRole('button', {
          name: FILTER_POSITION_SPOKEN[position],
          selected: position === saved,
        }),
      ).toBeTruthy();
    }
  }

  it('offers Off, At least Medium and At least High — off by default, with no hides line', async () => {
    await openReliability();

    expectSaved('OFF');
    expect(screen.queryByText(hidesLine({ hides: 0, of: 11 }))).toBeNull();
    expect(screen.queryByText(/dealt with everyone again/)).toBeNull();
  });

  /**
   * **The tap writes, the re-read settles.** *At least High* sends `{ minimum: 'HIGH' }`; the
   * `204` has no body, so what is drawn afterwards — the raised segment and *hides 2 of the 11* —
   * is the record read again. Then *Off* sends `null` and the line goes.
   */
  it('writes the position tapped, and shows the position and the hides line the re-read says are saved', async () => {
    let saved: Wire['ReliabilityFilterSchema'] = FILTER_OFF;
    transport.on('GET', OWN_RECORD_PATH, () =>
      json({ ...OWN_RECORD_SERVED, reliability: { ...SERGIO_RELIABILITY, filter: saved } }),
    );
    transport.on('PUT', FILTER_PATH, (request) => {
      const { minimum } = request.body as Wire['SetReliabilityFilterRequest'];
      saved = minimum === null ? FILTER_OFF : { ...MARTA_FILTER, minimum };
      return noContent();
    });
    await openReliability();

    fireEvent.press(segment('HIGH'));

    expect(await screen.findByText(hidesLine({ hides: 2, of: 11 }))).toBeTruthy();
    expect(transport.requestsTo('PUT', FILTER_PATH).map((r) => r.body)).toEqual([
      { minimum: 'HIGH' },
    ]);
    expectSaved('HIGH');

    fireEvent.press(segment('OFF'));

    await waitFor(() => expect(screen.queryByText(hidesLine({ hides: 2, of: 11 }))).toBeNull());
    expect(transport.requestsTo('PUT', FILTER_PATH).map((r) => r.body)).toEqual([
      { minimum: 'HIGH' },
      { minimum: null },
    ]);
    expectSaved('OFF');
  });

  it('writes nothing for a tap on the position already saved', async () => {
    transport.on('PUT', FILTER_PATH, () => noContent());
    await openReliability();

    fireEvent.press(segment('OFF'));

    expect(transport.requestsTo('PUT', FILTER_PATH)).toEqual([]);
  });

  /** A saved filter is drawn as saved: the raised segment and its line, from the record alone. */
  it('draws a filter that is on as the record says it is saved', async () => {
    serveOwnRecord(MARTA_FILTER);
    await openReliability();

    expectSaved('HIGH');
    expect(screen.getByText('Your filter hides 2 of the 11 players in your groups.')).toBeTruthy();
  });

  /** A refusal says so, and the segment falls back to what the record says — nothing is guessed. */
  it('says so when the save is refused, and the switch falls back to what is saved', async () => {
    transport.on('PUT', FILTER_PATH, () => errorResponse(409, 'concurrent_modification'));
    await openReliability();

    fireEvent.press(segment('MEDIUM'));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expectSaved('OFF');
    expect(screen.queryByText(/Your filter hides/)).toBeNull();
  });

  /**
   * **Sergio, at 69, reads the sentence that names nobody** — the band and the figure back — under
   * his own switch, which is off. Marta, whom nobody filters, never sees it.
   */
  it('tells a hidden player, naming nobody, the band and the figure that brings them back', async () => {
    transport.on('GET', OWN_RECORD_PATH, () =>
      json({
        ...OWN_RECORD_SERVED,
        reliability: {
          ...SERGIO_RELIABILITY,
          player_score: 69,
          band: 'MEDIUM',
          filter: HIDDEN_BY_A_HIGH_FILTER,
        },
      }),
    );
    await openReliability(reliabilityLine({ playerScore: 69, band: 'MEDIUM', isNew: false }));

    expect(
      screen.getByText(
        'Some players in your groups play only with High reliability or above. At 75 you’re dealt with everyone again.',
      ),
    ).toBeTruthy();
    expect(screen.getByText(backWithEveryoneLine({ band: 'HIGH', points: 75 }))).toBeTruthy();
    expectSaved('OFF');
  });
});

// ---------------------------------------------------------------------------
// How others see you
// ---------------------------------------------------------------------------

/**
 * **The sheet behind the tab's door reads the same row** — the sheet is `PlayerRecordSheet`
 * whole, and the builder's walk holds it to the figure on your own face; what is proved here
 * is the door the spec names, so that *He opens How others see you and reads it there too*
 * (#473) is a sentence a test says.
 */
describe('How others see you', () => {
  it('draws the sportsmanship figure and its count on your own record, and no band word', async () => {
    await onYou();
    fireEvent.press(
      screen.getByLabelText(doorRowLabel(HOW_OTHERS_SEE_YOU_TITLE, HOW_OTHERS_SEE_YOU_LINE)),
    );
    await screen.findByRole('header', { name: OWN_RECORD_TITLE });
    // The block says what the reliability screen says: the points and the band's word.
    expect(
      await screen.findByLabelText(
        recordBlocksLabel({
          reliability: { playerScore: 75, band: 'HIGH', isNew: false },
          lastFive: ['WIN', 'LOSS', 'WIN', 'WIN', 'LOSS'],
          countedGames: 9,
        }),
      ),
    ).toBeTruthy();
    // The card is folded under *Full record* on the sheet, as on anybody's.
    fireEvent.press(await screen.findByRole('button', { name: FULL_RECORD }));

    expect(await screen.findByText('turned up 12 of 13')).toBeTruthy();
    expect(screen.getByText(SPORTSMANSHIP_LABEL)).toBeTruthy();
    expect(screen.getByText(opinionFigure({ average: 4.3, raters: 12 }))).toBeTruthy();
    expect(screen.queryByText(/^(Good|Mixed|Poor)$/)).toBeNull();
  });
});
