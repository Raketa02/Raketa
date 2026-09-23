/**
 * **The You tab's words this feature owns** — `the-words.md` §27, the record's rows and the
 * two read-only screens.
 *
 * The passport's cards are the result screen's and the reliability screen's rows are the
 * record card's, so their sentences are asserted where they live. What is new is the two rows'
 * live lines, the passport's chip and card words, the ring's word on the reliability screen,
 * and the one sentence a player with no record is told.
 */

import type { Reliability } from '../domain/playerRecord';

import { OWN_RECORD_TITLE, PLAYER_SCORE_BLOCK } from './recordPresentation';
import {
  ADD_A_SPORT,
  ADD_A_SPORT_BODY,
  HOW_OTHERS_SEE_YOU_LINE,
  HOW_OTHERS_SEE_YOU_TITLE,
  NOTHING_COUNTED,
  OUT_OF_100,
  PLAYER_RELIABILITY_TITLE,
  SCORE_LABEL,
  SCORE_TONE_WORD,
  SKILL_PASSPORT_TITLE,
  THE_LADDER,
  ladderRung,
  passportLine,
  rateSportChip,
  reliabilityLine,
  scoreRingLabel,
  statusChipVariant,
} from './youRecordPresentation';

const RELIABILITY: Reliability = {
  playerScore: 92,
  strands: [
    { strand: 'SHOWS_UP', good: 11, opportunities: 12, pct: 92 },
    { strand: 'ANSWERS_CHALLENGES', good: 6, opportunities: 7, pct: 86 },
    { strand: 'ANSWERS_RESULTS', good: 5, opportunities: 5, pct: 100 },
  ],
};

describe('the two rows', () => {
  it('names the passport, and lists each rating with its level', () => {
    expect(SKILL_PASSPORT_TITLE).toBe('Skill passport');
    expect(
      passportLine([
        { sport: 'padel', level: 2.71 },
        { sport: 'tennis', level: 3.1 },
      ]),
    ).toBe('Padel 2,71 · Tennis 3,10');
  });

  it('names reliability by the block’s own word, and counts what is behind the score', () => {
    expect(PLAYER_RELIABILITY_TITLE).toBe(PLAYER_SCORE_BLOCK);
    expect(reliabilityLine(RELIABILITY)).toBe('92 of 100 · 3 things counted');
    expect(reliabilityLine({ playerScore: 70, strands: [RELIABILITY.strands[0]!] })).toBe(
      '70 of 100 · 1 thing counted',
    );
  });

  it('says what an absent record is, rather than drawing a nought', () => {
    expect(reliabilityLine(undefined)).toBe('Nothing counted yet');
  });

  it('opens your own record under the sheet’s own title, cited', () => {
    expect(HOW_OTHERS_SEE_YOU_TITLE).toBe(OWN_RECORD_TITLE);
    expect(HOW_OTHERS_SEE_YOU_LINE).toBe('Your player record, as a stranger reads it');
  });
});

describe('the reliability screen', () => {
  /** The tone ladder's three steps, said — `scoreTone`'s bounds, one word each. */
  it('gives each step of the tone ladder a word, and the scale under it', () => {
    expect(SCORE_TONE_WORD).toEqual({
      good: 'Reliable',
      neutral: 'Holding',
      poor: 'Under the bar',
    });
    expect(OUT_OF_100).toBe('Out of 100');
  });

  it('names the ring by the block’s word and the scale, as the sheet’s pill does', () => {
    expect(scoreRingLabel(92)).toBe('Player reliability 92 out of 100');
  });

  it('tells a player with no record that there is no score, and that it is not a low one', () => {
    expect(NOTHING_COUNTED).toMatch(/not a low one/);
    expect(NOTHING_COUNTED).not.toMatch(/\b0\b/);
  });

  it('labels the header card’s ring with the one word under it', () => {
    expect(SCORE_LABEL).toBe('Score');
  });
});

describe('the passport', () => {
  /** A `Tag`, not a row: on-dark for an estimate, amber while calibrating, mint once stable. */
  it('draws the status chip in the tone the status has', () => {
    expect(statusChipVariant('initial_estimate')).toBe('onDark');
    expect(statusChipVariant('calibrating')).toBe('warn');
    expect(statusChipVariant('stable')).toBe('ok');
    // A status this build has never heard of is drawn plainly, as its label is.
    expect(statusChipVariant('provisional')).toBe('onDark');
  });

  it('offers a sport as its own questionnaire, and promises nothing held will change', () => {
    expect(ADD_A_SPORT).toBe('Add a sport');
    expect(ADD_A_SPORT_BODY).toBe(
      'One questionnaire, one rating. Nothing you already hold changes.',
    );
    expect(rateSportChip('badminton')).toBe('Rate Badminton');
  });

  it('marks the player’s own rung on the ladder with their sports', () => {
    expect(THE_LADDER).toBe('The ladder');
    expect(ladderRung('Established', ['padel', 'squash'])).toBe(
      'Established · you (padel, squash)',
    );
    expect(ladderRung('Advanced', [])).toBe('Advanced');
  });
});
