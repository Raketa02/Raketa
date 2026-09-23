import { SCORE_FLOOR, SCORE_STRONG, scoreTone } from './scoreTone';

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
