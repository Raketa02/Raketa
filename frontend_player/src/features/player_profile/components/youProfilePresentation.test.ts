/**
 * The You tab's words this feature owns — `the-words.md` §27, held to the table.
 *
 * Most of the tab's sentences are citations of the steps' own, and those are asserted where
 * they live. What is new is the live lines, the few sentences a screen gained or lost on the
 * way from a step to a row, and the five rows whose screens land with their contract — which
 * must name what they are and never *coming soon* (10.1's rule).
 */

import { PHOTO_CEILING } from '../domain/photoCollection';

import { RADIUS_LABEL, radiusWords } from './radiusPresentation';
import {
  AREA_LINE,
  AREA_SET,
  CLEAR_ALL,
  DEFERRED_ROW,
  HOW_FAR_TO_LOOK_TITLE,
  KIND_OF_GAME_LINE,
  NO_INTRO_LINE,
  READ_AGAIN,
  REMOVE_INTRO,
  SAVE,
  SAVED,
  SAVE_YOUR_WEEK,
  introLine,
  kindOfGameLine,
  photosLine,
  radiusLine,
  tagsLine,
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

describe('the live lines on your card', () => {
  it('counts the photos against the ceiling and says whether the profile photo passed the check', () => {
    // *On court* only of a photo the check passed: a flagged one and one nobody looked at
    // (ADR-0138) both read as not checked, and neither is a claim about the photograph.
    expect(photosLine([{ photoId: 'a', review: 'allowed' }, { photoId: 'b' }])).toBe(
      `2 of ${PHOTO_CEILING} · profile photo on court`,
    );
    expect(photosLine([{ photoId: 'a', review: 'flagged' }])).toBe(
      `1 of ${PHOTO_CEILING} · profile photo not checked as on court`,
    );
    expect(photosLine([{ photoId: 'a' }, { photoId: 'b', review: 'allowed' }])).toBe(
      `2 of ${PHOTO_CEILING} · profile photo not checked as on court`,
    );
  });

  it('says a court poster stands in where there is no photo', () => {
    expect(photosLine([])).toBe('None — a court poster stands in');
  });

  it('counts the tags against the served ceiling and names the first two, the rest as a count', () => {
    expect(
      tagsLine(['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN', 'WARMS_UP_PROPERLY', 'HERE_TO_IMPROVE'], 6),
    ).toBe('4 of 6 · Stays for a drink, Plays to win, +2');
    expect(tagsLine(['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN'], 6)).toBe(
      '2 of 6 · Stays for a drink, Plays to win',
    );
    // The names, never the emoji — a live line is one line of `tiny`.
    expect(tagsLine(['PLAYS_TO_WIN'], 5)).toBe('1 of 5 · Plays to win');
    expect(tagsLine(['PLAYS_TO_WIN'], 5)).not.toMatch(/🏆/u);
  });

  it('quotes the intro, and quotes the step’s title where there is none', () => {
    expect(introLine('Will travel for a hard game.')).toBe('“Will travel for a hard game.”');
    expect(introLine(undefined)).toBe(NO_INTRO_LINE);
    expect(NO_INTRO_LINE).toBe('None — say it in your own words');
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

  it('withdraws the intro with its own control, beside Save', () => {
    expect(REMOVE_INTRO).toBe('Remove intro');
  });
});

describe('the two rows whose screens land with their contract', () => {
  it('are the two #472 draws — the three social edits have their screens', () => {
    expect(Object.keys(DEFERRED_ROW).sort()).toEqual(['gameSuggestions', 'whoYouPlayWith']);
  });

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
