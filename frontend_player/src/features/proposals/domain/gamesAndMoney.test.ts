/**
 * The two limits' rules: the stepper stays inside the range the server offers, a change keeps the
 * other value as it stands, and the week's money bound is the games times the ceiling — or none
 * while the ceiling is off.
 */

import {
  canStep,
  limitsOf,
  sameLimits,
  steppedGames,
  weeklyBoundGrosze,
  withCeiling,
  withGames,
  type GamesAndMoney,
} from './gamesAndMoney';

const HELD: GamesAndMoney = {
  gamesPerWeek: 4,
  mostIllPayGrosze: null,
  gamesPerWeekRange: { least: 1, most: 7 },
  ceilingChoicesGrosze: [3500, 4500, 6000],
};

describe('the games-per-week stepper', () => {
  it('steps one game at a time', () => {
    expect(steppedGames(HELD, 1)).toBe(5);
    expect(steppedGames(HELD, -1)).toBe(3);
  });

  it('is clamped to the range the server offers', () => {
    const most = withGames(HELD, 7);
    const least = withGames(HELD, 1);

    expect(steppedGames(most, 1)).toBe(7);
    expect(canStep(most, 1)).toBe(false);
    expect(canStep(most, -1)).toBe(true);

    expect(steppedGames(least, -1)).toBe(1);
    expect(canStep(least, -1)).toBe(false);
    expect(canStep(least, 1)).toBe(true);
  });

  it('reads the range off the server, never a range of its own', () => {
    const narrower = { ...HELD, gamesPerWeekRange: { least: 2, most: 4 } };
    expect(canStep(narrower, 1)).toBe(false);
    expect(steppedGames(withGames(narrower, 2), -1)).toBe(2);
  });

  it('pulls a value the range no longer holds back inside it', () => {
    const outside = { ...HELD, gamesPerWeek: 9 };
    expect(steppedGames(outside, -1)).toBe(7);
  });
});

describe('a change keeps the other value', () => {
  it('changes the games and leaves the ceiling', () => {
    const capped = withCeiling(HELD, 4500);
    expect(withGames(capped, 2)).toEqual({ ...HELD, gamesPerWeek: 2, mostIllPayGrosze: 4500 });
  });

  it('changes the ceiling, and Off is null', () => {
    expect(withCeiling(HELD, 3500).mostIllPayGrosze).toBe(3500);
    expect(withCeiling(withCeiling(HELD, 3500), null)).toEqual(HELD);
  });
});

describe('the pair a save sends', () => {
  it('is the two values, without the form’s offer', () => {
    expect(limitsOf(HELD)).toEqual({ gamesPerWeek: 4, mostIllPayGrosze: null });
  });

  it('is the same pair when both values are', () => {
    expect(sameLimits(HELD, limitsOf(HELD))).toBe(true);
    expect(sameLimits(HELD, withGames(HELD, 5))).toBe(false);
    expect(sameLimits(HELD, withCeiling(HELD, 3500))).toBe(false);
  });
});

describe('the week’s money bound', () => {
  it('is the games a week times the most per game', () => {
    expect(weeklyBoundGrosze(withCeiling(HELD, 4500))).toBe(18_000);
    expect(weeklyBoundGrosze(withGames(withCeiling(HELD, 3500), 1))).toBe(3500);
  });

  it('is none while the ceiling is off', () => {
    expect(weeklyBoundGrosze(HELD)).toBeUndefined();
  });
});
