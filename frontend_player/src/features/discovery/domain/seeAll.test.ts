import { joinPages, pageSport, pillChoices } from './seeAll';

describe('pageSport — the sport See all asks for', () => {
  it('is none for All, and the sport otherwise', () => {
    expect(pageSport('all')).toBeUndefined();
    expect(pageSport('squash')).toBe('squash');
  });
});

describe('joinPages — a See all list, page after page', () => {
  const person = (playerId: string) => ({ playerId });

  it('runs the pages in order, and draws a person once if two pages both hold them', () => {
    expect(
      joinPages([
        { people: [person('a'), person('b')], next: 'c', sports: [] },
        { people: [person('b'), person('c')], sports: [] },
      ]).map((one) => one.playerId),
    ).toEqual(['a', 'b', 'c']);
  });
});

describe('pillChoices — a See all pill (the mechanics §6.7, §7.4)', () => {
  it('opens with All, then the sports served', () => {
    expect(pillChoices(['padel', 'squash'], 'all')).toEqual(['all', 'padel', 'squash']);
  });

  it('keeps the chosen sport even once the read no longer offers it, in the sports’ order', () => {
    expect(pillChoices(['padel', 'badminton'], 'squash')).toEqual([
      'all',
      'padel',
      'squash',
      'badminton',
    ]);
  });
});
