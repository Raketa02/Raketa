import {
  SCORE_FLOOR,
  SCORE_RISKY,
  SCORE_STRONG,
  scoreBand,
  scoreTone,
  type ScoreBand,
  type ScoreTone,
} from './scoreTone';

/**
 * **The pill's ladder, at both boundaries and in both directions.**
 *
 * A threshold tested only from above is a threshold that can be moved by one without a
 * symptom, and the lower of these two is not a drawing decision: it is where the matcher
 * starts holding somebody back, so a pill that turned red one point late would tell a player
 * their penalty had not begun on the day it had.
 */
describe('the reliability pill’s tone', () => {
  it('turns poor exactly at the floor the matcher prices, and not a point either side', () => {
    expect(scoreTone(SCORE_FLOOR)).toBe('neutral');
    expect(scoreTone(SCORE_FLOOR - 1)).toBe('poor');
  });

  it('turns good exactly at the strong step, and not a point either side', () => {
    expect(scoreTone(SCORE_STRONG)).toBe('good');
    expect(scoreTone(SCORE_STRONG - 1)).toBe('neutral');
  });

  it('answers at both ends of the scale', () => {
    expect(scoreTone(0)).toBe('poor');
    expect(scoreTone(100)).toBe('good');
  });

  /**
   * The floor is the number the engine prices, and the pill exists so that a player who works
   * their record back up can watch the penalty lift. If the two ever differ, the screen is
   * lying about the one thing it was built to show.
   */
  it('reads the floor at the value the matcher itself uses', () => {
    expect(SCORE_FLOOR).toBe(70);
  });
});

/**
 * **The score tag's four bands**, at every boundary from both sides — and held to the ladder
 * above at every score, so the tag can never disagree with a meter on the record about which
 * side of the floor a number is on.
 */
describe('the score tag’s band', () => {
  it('is strong from the strong step up', () => {
    expect(scoreBand(100)).toBe('strong');
    expect(scoreBand(SCORE_STRONG)).toBe('strong');
    expect(scoreBand(SCORE_STRONG - 1)).toBe('ordinary');
  });

  it('is ordinary down to the floor the matcher prices', () => {
    expect(scoreBand(SCORE_FLOOR)).toBe('ordinary');
    expect(scoreBand(SCORE_FLOOR - 1)).toBe('wobbly');
  });

  it('is wobbly down to the risky step, and risky below it', () => {
    expect(scoreBand(SCORE_RISKY)).toBe('wobbly');
    expect(scoreBand(SCORE_RISKY - 1)).toBe('risky');
    expect(scoreBand(0)).toBe('risky');
  });

  it('reads the risky step at 50', () => {
    expect(SCORE_RISKY).toBe(50);
  });

  it('refines the tone ladder and never contradicts it, at every score', () => {
    const toneOf: Readonly<Record<ScoreBand, ScoreTone>> = {
      strong: 'good',
      ordinary: 'neutral',
      wobbly: 'poor',
      risky: 'poor',
    };
    for (let score = 0; score <= 100; score += 1) {
      expect(toneOf[scoreBand(score)]).toBe(scoreTone(score));
    }
  });
});
