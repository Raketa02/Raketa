/**
 * The You tab's words this feature owns — `the-words.md` §27, held to the table.
 *
 * Most of the tab's sentences are citations of the steps' own, and those are asserted where
 * they live. What is new is the live lines and the few sentences a screen gained or lost on
 * the way from a step to a row.
 */

import { PHOTO_CEILING } from '../domain/photoCollection';

import {
  AREA_LINE,
  AREA_SET,
  CLEAR_ALL,
  KIND_OF_GAME_LINE,
  NO_INTRO_LINE,
  REMOVE_INTRO,
  SAVE,
  SAVED,
  SAVE_YOUR_WEEK,
  introLine,
  kindOfGameLine,
  photosLine,
  tagsLine,
  weekLine,
  whoYouPlayWithLine,
} from './youProfilePresentation';

describe('the live lines', () => {
  it('counts the week, and says what an empty one means', () => {
    expect(weekLine([])).toBe('Nothing ticked — we do not know when you play');
    expect(weekLine([{ day: 1, hour: 9 }])).toBe('1 hour ticked');
    expect(
      weekLine([
        { day: 1, hour: 9 },
        { day: 6, hour: 19 },
      ]),
    ).toBe('2 hours ticked');
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

describe('the live lines that gate the matcher', () => {
  it('says who the player is matched with, and never what they answered about themselves', () => {
    // The preference only: the gender is drawn on its own screen and nowhere else on the tab.
    expect(whoYouPlayWithLine('any')).toBe('Matched with anyone');
    expect(whoYouPlayWithLine('women-only')).toBe('Matched with women only');
    expect(whoYouPlayWithLine('men-only')).toBe('Matched with men only');
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
      tagsLine(['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN', 'WARMS_UP_PROPERLY', 'HERE_TO_IMPROVE'], 8),
    ).toBe('4 of 8 · Stays for a drink, Plays to win, +2');
    expect(tagsLine(['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN'], 8)).toBe(
      '2 of 8 · Stays for a drink, Plays to win',
    );
    // A full eight, two of them new (ADR-0207 §7).
    expect(
      tagsLine(
        [
          'STAYS_FOR_A_COFFEE',
          'KEEPS_IN_TOUCH',
          'PLAYS_TO_WIN',
          'WARMS_UP_PROPERLY',
          'HAPPY_TO_SHARE_TIPS',
          'HERE_TO_IMPROVE',
          'HERE_TO_COMPETE',
          'NEW_IN_TOWN',
        ],
        8,
      ),
    ).toBe('8 of 8 · Stays for a coffee, Keeps in touch, +6');
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
  it('says the one thing the declaration section’s heading and body said', () => {
    expect(KIND_OF_GAME_LINE).toBe('This changes how people find you');
  });

  it('saves only on a button, and says so on the button', () => {
    expect(SAVE_YOUR_WEEK).toBe('Save your week');
    expect(SAVE).toBe('Save');
    expect(SAVED).toBe('Saved');
    expect(CLEAR_ALL).toBe('Clear all');
  });

  it('draws the area as set', () => {
    expect(AREA_SET).toBe('Your area is set');
  });

  it('withdraws the intro with its own control, beside Save', () => {
    expect(REMOVE_INTRO).toBe('Remove intro');
  });
});
