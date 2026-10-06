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
 * sport* drawn and inert, the ladder printing only the edges it was sent; the ring's word and
 * the record card on one screen, and the one sentence a player with no record is told.
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
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import {
  COUNTED_BLOCK,
  FULL_RECORD,
  LAST_FIVE_BLOCK,
  OWN_RECORD_TITLE,
  PLAYER_SCORE_BLOCK,
  SPORTSMANSHIP_LABEL,
  STRAND_NAME,
  VARIETY_LABEL,
  opinionFigure,
  recordBlocksLabel,
} from './recordPresentation';
import {
  ADD_A_SPORT,
  HOW_OTHERS_SEE_YOU_LINE,
  HOW_OTHERS_SEE_YOU_TITLE,
  NOTHING_COUNTED,
  OUT_OF_100,
  PLAYER_RELIABILITY_TITLE,
  SCORE_TONE_WORD,
  SKILL_PASSPORT_TITLE,
  THE_LADDER,
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
          playerScore: 92,
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
  const RELIABILITY_LINE = reliabilityLine({
    playerScore: 92,
    strands: [
      { strand: 'SHOWS_UP', good: 11, opportunities: 12, pct: 92 },
      { strand: 'ANSWERS_CHALLENGES', good: 6, opportunities: 7, pct: 86 },
      { strand: 'ANSWERS_RESULTS', good: 5, opportunities: 5, pct: 100 },
    ],
  });

  async function openReliability() {
    await onYou();
    fireEvent.press(
      await screen.findByLabelText(doorRowLabel(PLAYER_RELIABILITY_TITLE, RELIABILITY_LINE)),
    );
    await screen.findByRole('header', { name: PLAYER_RELIABILITY_TITLE });
  }

  it('draws the score in the ring with the tone ladder’s word, then the record card’s rows', async () => {
    await openReliability();

    expect(await screen.findByLabelText(scoreRingLabel(92))).toBeTruthy();
    expect(screen.getByText(SCORE_TONE_WORD.good)).toBeTruthy();
    expect(screen.getByText(OUT_OF_100)).toBeTruthy();
    // The card, as the sheet draws it: the strands, the variety, the sportsmanship — the
    // figure, since #468 serves it to the subject as to anybody (ADR-0179 §5), and no band
    // word anywhere on the screen (#473; the three are spelled only to be asserted absent).
    expect(screen.getByText(STRAND_NAME.SHOWS_UP)).toBeTruthy();
    expect(screen.getByText('11 of 12')).toBeTruthy();
    expect(screen.getByText(VARIETY_LABEL)).toBeTruthy();
    expect(screen.getByText(SPORTSMANSHIP_LABEL)).toBeTruthy();
    expect(screen.getByText(opinionFigure({ average: 4.3, raters: 12 }))).toBeTruthy();
    expect(screen.queryByText(/^(Good|Mixed|Poor)$/)).toBeNull();
  });

  it('gives a score under the bar its own word', async () => {
    stubOwnRecord(transport, {
      ...OWN_RECORD_SERVED,
      reliability: {
        player_score: 64,
        strands: [{ strand: 'SHOWS_UP', good: 5, opportunities: 8, pct: 63 }],
      },
    });
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));
    fireEvent.press(await screen.findByLabelText(PLAYER_RELIABILITY_TITLE, { exact: false }));

    expect(await screen.findByText(SCORE_TONE_WORD.poor)).toBeTruthy();
  });

  it('tells a player with no record that there is no score, and that it is not a low one', async () => {
    const { reliability: _none, ...noRecord } = OWN_RECORD_SERVED;
    stubOwnRecord(transport, noRecord);
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));
    fireEvent.press(
      await screen.findByLabelText(
        doorRowLabel(PLAYER_RELIABILITY_TITLE, reliabilityLine(undefined)),
      ),
    );

    expect(await screen.findByText(NOTHING_COUNTED)).toBeTruthy();
    expect(screen.queryByLabelText(/out of 100/)).toBeNull();
    // The variety is a different absence, and is still drawn.
    expect(screen.getByText(VARIETY_LABEL)).toBeTruthy();
  });

  /**
   * **A player nobody has rated draws no sportsmanship row, as before** — the fourth absence,
   * asking its own question: the rows above it are still drawn, and nothing is drawn at nought.
   */
  it('draws no sportsmanship row for a player nobody has rated', async () => {
    const { sportsmanship: _nobody, ...unrated } = OWN_RECORD_SERVED;
    stubOwnRecord(transport, unrated);
    await openReliability();

    expect(await screen.findByText(STRAND_NAME.SHOWS_UP)).toBeTruthy();
    expect(screen.getByText(VARIETY_LABEL)).toBeTruthy();
    expect(screen.queryByText(SPORTSMANSHIP_LABEL)).toBeNull();
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
    // The card is folded under *Full record* on the sheet, as on anybody's.
    fireEvent.press(await screen.findByRole('button', { name: FULL_RECORD }));

    expect(await screen.findByText(SPORTSMANSHIP_LABEL)).toBeTruthy();
    expect(screen.getByText(opinionFigure({ average: 4.3, raters: 12 }))).toBeTruthy();
    expect(screen.queryByText(/^(Good|Mixed|Poor)$/)).toBeNull();
  });
});
