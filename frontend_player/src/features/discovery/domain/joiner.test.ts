import { joinPages, joinedAgo, pageSport, pillChoices, type Joiner } from './joiner';

describe('joinedAgo — the Joined ladder, in Warsaw days (the mechanics §7.3)', () => {
  it.each<[number, ReturnType<typeof joinedAgo>]>([
    [0, { kind: 'today' }],
    [1, { kind: 'yesterday' }],
    [2, { kind: 'days', days: 2 }],
    [6, { kind: 'days', days: 6 }],
    [7, { kind: 'lastWeek' }],
    [13, { kind: 'lastWeek' }],
    [14, { kind: 'weeks', weeks: 2 }],
    [20, { kind: 'weeks', weeks: 2 }],
    [21, { kind: 'weeks', weeks: 3 }],
    [27, { kind: 'weeks', weeks: 3 }],
    [28, { kind: 'weeks', weeks: 4 }],
    [30, { kind: 'weeks', weeks: 4 }],
  ])('%i days', (days, ago) => {
    expect(joinedAgo(days)).toEqual(ago);
  });

  it('never says more than four weeks, nor less than today', () => {
    expect(joinedAgo(45)).toEqual({ kind: 'weeks', weeks: 4 });
    expect(joinedAgo(-1)).toEqual({ kind: 'today' });
  });
});

describe('pageSport — the sport See all asks for', () => {
  it('is none for All, and the sport otherwise', () => {
    expect(pageSport('all')).toBeUndefined();
    expect(pageSport('squash')).toBe('squash');
  });
});

describe('joinPages — See all’s grid, page after page', () => {
  const joiner = (playerId: string): Joiner => ({
    playerId,
    nickname: playerId,
    daysSinceJoined: 1,
    sports: [],
    relation: 'NONE',
  });

  it('runs the pages in order, and draws a person once if two pages both hold them', () => {
    expect(
      joinPages([
        { joiners: [joiner('a'), joiner('b')], next: 'c', sports: [] },
        { joiners: [joiner('b'), joiner('c')], sports: [] },
      ]).map((one) => one.playerId),
    ).toEqual(['a', 'b', 'c']);
  });
});

describe('pillChoices — the See all pill (the mechanics §7.4)', () => {
  it('opens with All, then the sports served', () => {
    expect(pillChoices(['padel', 'squash'], 'all')).toEqual(['all', 'padel', 'squash']);
  });

  it('keeps the chosen sport even once nobody new holds a level in it, in the sports’ order', () => {
    expect(pillChoices(['padel', 'badminton'], 'squash')).toEqual([
      'all',
      'padel',
      'squash',
      'badminton',
    ]);
  });
});
