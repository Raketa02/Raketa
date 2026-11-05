import { intentChangeCost, sportToCount, type DeckCounts } from './intentChangeCost';

/** Ania's padel: seven competitive cards across her groups, none for fun. */
const SEVEN_COMPETITIVE: DeckCounts = { competitive: 7, forFun: 0 };

describe('what an answer on What kind of game costs', () => {
  describe('to a single kind', () => {
    it('drops the other kind, from the other kind, counting the cards that go', () => {
      expect(intentChangeCost('COMPETITIVE', 'FOR_FUN', SEVEN_COMPETITIVE)).toEqual({
        change: 'drops',
        kind: 'competitive',
        count: 7,
      });
      expect(intentChangeCost('FOR_FUN', 'COMPETITIVE', { competitive: 0, forFun: 3 })).toEqual({
        change: 'drops',
        kind: 'forFun',
        count: 3,
      });
    });

    /** Going from *Either suits me* to *For fun* counts the competitive cards: the kind that goes. */
    it('drops the other kind from Either suits me, counting that kind', () => {
      const both: DeckCounts = { competitive: 4, forFun: 2 };

      expect(intentChangeCost('NO_PREFERENCE', 'FOR_FUN', both)).toEqual({
        change: 'drops',
        kind: 'competitive',
        count: 4,
      });
      expect(intentChangeCost('NO_PREFERENCE', 'COMPETITIVE', both)).toEqual({
        change: 'drops',
        kind: 'forFun',
        count: 2,
      });
    });

    /** A count nobody has read is not zero — zero is a wording of its own. */
    it('has no count while the counts are not in hand', () => {
      expect(intentChangeCost('COMPETITIVE', 'FOR_FUN', undefined)).toEqual({
        change: 'drops',
        kind: 'competitive',
        count: undefined,
      });
    });
  });

  it('keeps the kind played and adds the other, to Either suits me, with no count', () => {
    expect(intentChangeCost('COMPETITIVE', 'NO_PREFERENCE', SEVEN_COMPETITIVE)).toEqual({
      change: 'widens',
      keeps: 'competitive',
      gets: 'forFun',
    });
    expect(intentChangeCost('FOR_FUN', 'NO_PREFERENCE', undefined)).toEqual({
      change: 'widens',
      keeps: 'forFun',
      gets: 'competitive',
    });
  });

  it('costs nothing to give the answer already held', () => {
    expect(intentChangeCost('COMPETITIVE', 'COMPETITIVE', SEVEN_COMPETITIVE)).toBeUndefined();
    expect(intentChangeCost('FOR_FUN', 'FOR_FUN', SEVEN_COMPETITIVE)).toBeUndefined();
    expect(intentChangeCost('NO_PREFERENCE', 'NO_PREFERENCE', SEVEN_COMPETITIVE)).toBeUndefined();
  });

  /** An undeclared sport deals nothing, so no answer to it takes anything away (ADR-0201 §6). */
  it('says nothing about a sport with no answer yet', () => {
    expect(intentChangeCost(undefined, 'FOR_FUN', SEVEN_COMPETITIVE)).toBeUndefined();
    expect(intentChangeCost(undefined, 'NO_PREFERENCE', SEVEN_COMPETITIVE)).toBeUndefined();
  });
});

describe('which sport is counted', () => {
  const declarations = { padel: 'COMPETITIVE', tennis: 'NO_PREFERENCE' } as const;

  it('counts the open row’s sport while it is declared', () => {
    expect(sportToCount('padel', declarations)).toBe('padel');
    expect(sportToCount('tennis', declarations)).toBe('tennis');
  });

  it('counts nothing with no row open, an undeclared row open, or no declarations read', () => {
    expect(sportToCount(undefined, declarations)).toBeUndefined();
    expect(sportToCount('squash', declarations)).toBeUndefined();
    expect(sportToCount('padel', undefined)).toBeUndefined();
  });
});
