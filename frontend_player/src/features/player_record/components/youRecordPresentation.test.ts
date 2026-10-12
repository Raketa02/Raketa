/**
 * **The You tab's words this feature owns** — `the-words.md` §27, the record's rows and the
 * two read-only screens.
 *
 * The passport's cards are the result screen's and the reliability screen's rows are the
 * record card's, so their sentences are asserted where they live. What is new is the two rows'
 * live lines, the passport's chip and card words, the word beside the figure on the reliability
 * screen, and the one sentence a new player is told.
 */

import { OWN_RECORD_TITLE, PLAYER_SCORE_BLOCK } from './recordPresentation';
import {
  ADD_A_SPORT,
  ADD_A_SPORT_BODY,
  HOW_OTHERS_SEE_YOU_LINE,
  HOW_OTHERS_SEE_YOU_TITLE,
  NEW_PLAYER_NOTE,
  OUT_OF_100,
  PLAYER_RELIABILITY_TITLE,
  SCORE_LABEL,
  SKILL_PASSPORT_TITLE,
  THE_LADDER,
  ladderRung,
  passportLine,
  rateSportChip,
  reliabilityLine,
  reliabilityWord,
  scoreRingLabel,
  statusChipVariant,
} from './youRecordPresentation';

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

  /** The sheet's own head, written in (`the-words.md` §27, ADR-0195): points and the band. */
  it('names reliability by the block’s own word, and reads the points and the band', () => {
    expect(PLAYER_RELIABILITY_TITLE).toBe(PLAYER_SCORE_BLOCK);
    expect(reliabilityLine({ playerScore: 75, band: 'HIGH', isNew: false })).toBe('75 · High');
    expect(reliabilityLine({ playerScore: 100, band: 'VERY_HIGH', isNew: true })).toBe('100 · New');
  });

  it('opens your own record under the sheet’s own title, cited', () => {
    expect(HOW_OTHERS_SEE_YOU_TITLE).toBe(OWN_RECORD_TITLE);
    expect(HOW_OTHERS_SEE_YOU_LINE).toBe('Your player record, as a stranger reads it');
  });
});

describe('the reliability screen', () => {
  /**
   * **The band said in full, beside the figure** — *Very high*, *High*, *Medium* or *Low
   * reliability*, keyed by the served code, and *New* in its place for a player who is new. The
   * retired tone ladder's three words are spelled here only to be asserted absent.
   */
  it('says the band beside the figure, and New where it applies', () => {
    expect(reliabilityWord({ playerScore: 92, band: 'VERY_HIGH', isNew: false })).toBe(
      'Very high reliability',
    );
    expect(reliabilityWord({ playerScore: 75, band: 'HIGH', isNew: false })).toBe(
      'High reliability',
    );
    expect(reliabilityWord({ playerScore: 64, band: 'MEDIUM', isNew: false })).toBe(
      'Medium reliability',
    );
    expect(reliabilityWord({ playerScore: 40, band: 'LOW', isNew: false })).toBe('Low reliability');
    expect(reliabilityWord({ playerScore: 100, band: 'VERY_HIGH', isNew: true })).toBe('New');
    expect(reliabilityWord({ playerScore: 42, isNew: false })).toBeUndefined();
    expect(OUT_OF_100).toBe('Out of 100');
  });

  it('names the ring by the block’s word and the scale, as the sheet’s block does', () => {
    expect(scoreRingLabel(92)).toBe('Player reliability 92 out of 100');
  });

  /**
   * **The new player's sentence speaks of games, never of plans** (#660): everyone has a figure
   * from the start, so what a new player is told is where it starts and what *New* means — not
   * that nothing has fallen due.
   */
  it('tells a new player where the figure starts and what New means', () => {
    expect(NEW_PLAYER_NOTE).toBe(
      'Everyone starts at 100. Yours reads New until you’ve played 3 games through.',
    );
    expect(NEW_PLAYER_NOTE).not.toMatch(/plan/i);
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
