/**
 * **The Rankings page's words** ([#775](https://github.com/Raketa02/Raketa/issues/775)) — every
 * sentence as the words §30 write it, with the ordinals §30's placeholders spell, and the rule over
 * all of them: no sentence says *her*, *his*, *she* or *he* about another player (ADR-0096).
 */

import type { GapLine } from '../domain/ranking';

import {
  RANKINGS_COPY,
  cardChipWords,
  chipFace,
  gapLineParts,
  VIEW_WORDS,
  friendsCardLine,
  getYourLevelLabel,
  jumpButtonLabel,
  nobodyRankedLine,
  notListedLine,
  ordinal,
  placeCardSpoken,
  rankedRowLabel,
  trophyLabel,
  trophyPlace,
} from './rankingsCopy';

const said = (line: GapLine) =>
  gapLineParts(line)
    .map((part) => part.text)
    .join('');
const strong = (line: GapLine) =>
  gapLineParts(line)
    .filter((part) => part.strong === true)
    .map((part) => part.text);

describe('ordinals', () => {
  it('reads -st, -nd and -rd after a last digit of 1, 2 and 3, except after a ten', () => {
    const read = [1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 101, 111, 112, 212].map(ordinal);

    expect(read).toEqual([
      '1st',
      '2nd',
      '3rd',
      '4th',
      '11th',
      '12th',
      '13th',
      '21st',
      '22nd',
      '23rd',
      '101st',
      '111th',
      '112th',
      '212th',
    ]);
  });
});

describe('the trophy', () => {
  it('reads the place as a number, and nothing without one', () => {
    expect(trophyPlace(7)).toBe('#7');
    expect(trophyPlace(undefined)).toBeUndefined();
  });

  it('is named for the page it opens, with the place where there is one', () => {
    expect(trophyLabel('padel', 7, 'GENERAL')).toBe('Rankings, 7th in padel');
    expect(trophyLabel('padel', undefined, 'GENERAL')).toBe('Rankings');
  });

  // #777: the number is the remembered view's, so its name says which.
  it('names the Friends place as one among friends', () => {
    expect(trophyLabel('padel', 4, 'FRIENDS')).toBe('Rankings, 4th among your friends in padel');
    expect(trophyLabel('padel', undefined, 'FRIENDS')).toBe('Rankings');
  });
});

describe('the chip', () => {
  it('draws a mark and a count, a mark alone, or New', () => {
    expect(chipFace({ kind: 'UP', places: 2 })).toEqual({ mark: 'up', count: '2' });
    expect(chipFace({ kind: 'DOWN', places: 1 })).toEqual({ mark: 'down', count: '1' });
    expect(chipFace({ kind: 'SAME' })).toEqual({ mark: 'same' });
    expect(chipFace({ kind: 'NEW' })).toEqual({ word: 'New' });
  });

  it('speaks the card whole: the place, the level and the week', () => {
    expect(
      placeCardSpoken({ place: 7, of: 13, level: 2.71, chip: { kind: 'UP', places: 1 } }),
    ).toBe('your place: 7th of 13, 2,71, up 1 this week');
    expect(placeCardSpoken({ place: 1, of: 13, level: 3.4, chip: { kind: 'NEW' } })).toBe(
      'your place: 1st of 13, 3,40, new this week',
    );
    expect(placeCardSpoken({ place: 7, of: 13, level: 2.71 })).toBe('your place: 7th of 13, 2,71');
  });

  it('says what the week did beside it on the card', () => {
    expect(cardChipWords({ kind: 'UP', places: 1 })).toBe('up this week');
    expect(cardChipWords({ kind: 'DOWN', places: 1 })).toBe('down this week');
    expect(cardChipWords({ kind: 'SAME' })).toBe('no change this week');
    expect(cardChipWords({ kind: 'NEW' })).toBe('this week');
  });
});

describe('the gap line', () => {
  const below = { nickname: 'Zofia', gap: 0.02 };

  it('one win closes it', () => {
    const line: GapLine = {
      kind: 'between',
      above: { nickname: 'Karol', gap: 0.04, wins: 1, tied: false },
      below,
    };

    expect(said(line)).toBe('0,04 behind Karol · one win closes it · Zofia is 0,02 behind you');
    // The numbers are bold, as rankings 3 draws them.
    expect(strong(line)).toEqual(['0,04', '0,02']);
  });

  it('about n wins close it, from two to five', () => {
    const line: GapLine = {
      kind: 'between',
      above: { nickname: 'Karol', gap: 0.04, wins: 3, tied: false },
      below,
    };

    expect(said(line)).toBe('0,04 behind Karol · about 3 wins close it · Zofia is 0,02 behind you');
  });

  it('leaves the count out where the server sends none — above five wins', () => {
    const line: GapLine = {
      kind: 'between',
      above: { nickname: 'Karol', gap: 0.31, tied: false },
      below,
    };

    expect(said(line)).toBe('0,31 behind Karol · Zofia is 0,02 behind you');
  });

  it('level with the player above: one win puts you ahead', () => {
    const line: GapLine = {
      kind: 'between',
      above: { nickname: 'Ewa', gap: 0, tied: true },
      below,
    };

    expect(said(line)).toBe('Level with Ewa · one win puts you ahead · Zofia is 0,02 behind you');
  });

  it('the player below level with the reader', () => {
    const line: GapLine = {
      kind: 'between',
      above: { nickname: 'Karol', gap: 0.04, wins: 1, tied: false },
      below: { nickname: 'Zofia', gap: 0 },
    };

    expect(said(line)).toBe('0,04 behind Karol · one win closes it · Zofia is level with you');
  });

  it('in last place, only the part about the player above', () => {
    expect(
      said({ kind: 'between', above: { nickname: 'Karol', gap: 0.04, wins: 1, tied: false } }),
    ).toBe('0,04 behind Karol · one win closes it');
  });

  it('in first place, Top of the list, the whole line', () => {
    expect(said({ kind: 'top' })).toBe('Top of the list');
  });

  it('with nobody the reader can see above, only the part below', () => {
    expect(said({ kind: 'between', below })).toBe('Zofia is 0,02 behind you');
  });
});

describe('not listed in General', () => {
  it('counts the results still to play, the singular with one to go', () => {
    expect(
      notListedLine({ state: 'NEEDS_RESULTS', results: 2, resultsToEnter: 5 }, 'padel', 'GENERAL'),
    ).toBe('2 of 5 games — 3 more competitive padel games put you on the list');
    expect(
      notListedLine({ state: 'NEEDS_RESULTS', results: 0, resultsToEnter: 5 }, 'padel', 'GENERAL'),
    ).toBe('0 of 5 games — 5 more competitive padel games put you on the list');
    expect(
      notListedLine({ state: 'NEEDS_RESULTS', results: 4, resultsToEnter: 5 }, 'padel', 'GENERAL'),
    ).toBe('4 of 5 games — 1 more competitive padel game puts you on the list');
  });

  it('asks for a level first in a sport with none', () => {
    expect(notListedLine({ state: 'NO_LEVEL', resultsToEnter: 5 }, 'squash', 'GENERAL')).toBe(
      'No squash level yet — get one, then 5 competitive games put you on the list',
    );
    expect(getYourLevelLabel('squash')).toBe('Get your squash level');
  });

  it('says how to get back on, off the list', () => {
    expect(notListedLine({ state: 'OFF_THE_LIST' }, 'padel', 'GENERAL')).toBe(
      'Off the list — no competitive padel game in 90 days. Your next one puts you back.',
    );
  });
});

// §30.2 and §30.6 (#777).
describe('the Friends view', () => {
  it('names the switch’s two views', () => {
    expect(VIEW_WORDS).toEqual({ GENERAL: 'General', FRIENDS: 'Friends' });
  });

  it('says Just you so far, or that none of your friends is ranked, each with Add friends', () => {
    expect(friendsCardLine({ state: 'JUST_YOU' }, 'padel')).toBe('Just you so far');
    expect(friendsCardLine({ state: 'NO_FRIEND_LISTED' }, 'tennis')).toBe(
      'None of your friends is ranked in tennis yet',
    );
    expect(RANKINGS_COPY.addFriends).toBe('Add friends');
  });

  // §30.5: Friends takes one result, so a reader with a level and none reads the brief's line.
  it('says the first game puts the reader on the list, above the friends’ table', () => {
    expect(
      notListedLine({ state: 'NEEDS_RESULTS', results: 0, resultsToEnter: 1 }, 'padel', 'FRIENDS'),
    ).toBe('Not ranked in padel yet — your first confirmed competitive game puts you on the list');
  });

  it('asks for a level first, then one game', () => {
    expect(notListedLine({ state: 'NO_LEVEL', resultsToEnter: 1 }, 'squash', 'FRIENDS')).toBe(
      'No squash level yet — get one, then one competitive game puts you on the list',
    );
  });
});

describe('the list', () => {
  it('says so where nobody is ranked in the sport', () => {
    expect(nobodyRankedLine('badminton')).toBe('Nobody ranked in badminton yet');
  });

  it('names a row by its place, who, and the level — the reader’s own as You', () => {
    expect(rankedRowLabel({ place: 6, nickname: 'Karol', level: 2.75, isYou: false })).toBe(
      '6th, Karol, 2,75',
    );
    expect(rankedRowLabel({ place: 7, nickname: 'tomek.k', level: 2.71, isYou: true })).toBe(
      '7th, You, 2,71',
    );
  });

  // §30.7: the jump button (#776).
  it('names the jump button You and the reader’s place', () => {
    expect(jumpButtonLabel(212)).toBe('You · 212th');
    expect(jumpButtonLabel(1)).toBe('You · 1st');
  });
});

describe('no sentence says her, his, she or he', () => {
  it('holds over every sentence the page writes', () => {
    const sentences: readonly string[] = [
      ...Object.values(RANKINGS_COPY),
      said({
        kind: 'between',
        above: { nickname: 'Karol', gap: 0.04, wins: 3, tied: false },
        below: { nickname: 'Zofia', gap: 0 },
      }),
      said({ kind: 'between', above: { nickname: 'Ewa', gap: 0, tied: true } }),
      notListedLine({ state: 'NEEDS_RESULTS', results: 4, resultsToEnter: 5 }, 'padel', 'GENERAL'),
      notListedLine({ state: 'NO_LEVEL', resultsToEnter: 5 }, 'padel', 'GENERAL'),
      notListedLine({ state: 'OFF_THE_LIST' }, 'padel', 'GENERAL'),
      notListedLine({ state: 'NEEDS_RESULTS', results: 0, resultsToEnter: 1 }, 'padel', 'FRIENDS'),
      notListedLine({ state: 'NO_LEVEL', resultsToEnter: 1 }, 'padel', 'FRIENDS'),
      friendsCardLine({ state: 'JUST_YOU' }, 'padel'),
      friendsCardLine({ state: 'NO_FRIEND_LISTED' }, 'padel'),
      ...Object.values(VIEW_WORDS),
      trophyLabel('padel', 4, 'FRIENDS'),
      nobodyRankedLine('padel'),
      jumpButtonLabel(212),
    ];

    for (const sentence of sentences) {
      expect(sentence).not.toMatch(/\b(her|his|she|he|him)\b/i);
    }
  });
});
