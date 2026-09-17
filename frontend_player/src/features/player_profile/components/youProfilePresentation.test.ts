/**
 * The You tab's words this feature owns — `the-words.md` §27, held to the table.
 *
 * Most of the tab's sentences are citations of the steps' own, and those are asserted where
 * they live. What is new is the live lines, the few sentences a screen gained or lost on the
 * way from a step to a row, and the five rows whose screens land with their contract — which
 * must name what they are and never *coming soon* (10.1's rule).
 */

import { RADIUS_LABEL, radiusWords } from './radiusPresentation';
import {
  AREA_LINE,
  AREA_SET,
  CLEAR_ALL,
  DEFERRED_ROW,
  HOW_FAR_TO_LOOK_TITLE,
  KIND_OF_GAME_LINE,
  READ_AGAIN,
  SAVE,
  SAVED,
  SAVE_YOUR_WEEK,
  kindOfGameLine,
  radiusLine,
  weekLine,
} from './youProfilePresentation';

describe('the live lines', () => {
  it('counts the week, and says what an empty one means', () => {
    expect(weekLine([])).toBe('Nothing ticked — we do not know when you play');
    expect(weekLine([{ day: 1, part: 'morning' }])).toBe('1 slot ticked');
    expect(
      weekLine([
        { day: 1, part: 'morning' },
        { day: 6, part: 'evening' },
      ]),
    ).toBe('2 slots ticked');
  });

  it('reads the radius with the figure and the step’s own words', () => {
    expect(radiusLine(12)).toBe(`12 km · ${radiusWords(12)}`);
  });

  it('names the area’s one state, because a profile cannot be committed without one', () => {
    expect(AREA_LINE).toBe('Area set · updates when you open Raketa');
  });

  it('lists each rated sport with its answer, and says not set where there is none', () => {
    expect(
      kindOfGameLine([
        { sport: 'padel', intent: 'COMPETITIVE' },
        { sport: 'tennis', intent: 'FOR_FUN' },
        { sport: 'squash', intent: undefined },
      ]),
    ).toBe('Padel Competitive · Tennis For fun · Squash not set');
  });
});

describe('the titles and the buttons', () => {
  it('names the radius row with the step’s own label', () => {
    expect(HOW_FAR_TO_LOOK_TITLE).toBe(RADIUS_LABEL);
  });

  it('says the one thing the declaration section’s heading and body said', () => {
    expect(KIND_OF_GAME_LINE).toBe('This changes how people find you');
  });

  it('saves only on a button, and says so on the button', () => {
    expect(SAVE_YOUR_WEEK).toBe('Save your week');
    expect(SAVE).toBe('Save');
    expect(SAVED).toBe('Saved');
    expect(CLEAR_ALL).toBe('Clear all');
  });

  it('draws the area as set and offers to read it again', () => {
    expect(AREA_SET).toBe('Your area is set');
    expect(READ_AGAIN).toBe('Read my area again');
  });
});

describe('the five rows whose screens land with their contract', () => {
  /**
   * 10.1's empty-state rule: one present-tense line naming what the thing **is**, and never an
   * apology, a date, or a claim that nothing is happening.
   */
  it('names what each row is, on the row and behind it', () => {
    for (const row of Object.values(DEFERRED_ROW)) {
      expect(row.line.length).toBeGreaterThan(0);
      expect(row.screenLine.length).toBeGreaterThan(0);
      for (const sentence of [row.line, row.screenLine]) {
        expect(sentence).not.toMatch(/coming soon|soon|sorry|under construction|not built/i);
        expect(sentence).not.toMatch(/nothing is happening/i);
      }
    }
  });

  it('says on each screen that the edit lands with the read that carries the fact', () => {
    for (const row of Object.values(DEFERRED_ROW)) {
      expect(row.screenLine).toMatch(/profile read/);
    }
  });
});
