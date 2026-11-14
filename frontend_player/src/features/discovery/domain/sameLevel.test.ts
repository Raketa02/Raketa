import {
  foundAtSameLevel,
  levelGapOf,
  moreSportsOf,
  type LevelComparison,
  type SameLevelPlayer,
} from './sameLevel';

const PADEL: LevelComparison = {
  sport: 'padel',
  yourLevel: 2.71,
  theirLevel: 2.69,
  percentEven: 91,
  levelGap: -0.02,
  yourBand: 'Established',
};
const SQUASH: LevelComparison = { ...PADEL, sport: 'squash', percentEven: 51, levelGap: 0.25 };

const zofia = (sports: readonly LevelComparison[]): SameLevelPlayer => ({
  playerId: 'p-zofia',
  nickname: 'zofia.b',
  shown: sports[0]!,
  sports,
  relation: 'FRIEND',
});

describe('levelGapOf — the gap in words (the mechanics §6.4)', () => {
  it('is below you when theirs is lower, above you when higher, to the hundredth', () => {
    expect(levelGapOf(-0.02)).toEqual({ kind: 'below', gap: 0.02 });
    expect(levelGapOf(0.09)).toEqual({ kind: 'above', gap: 0.09 });
    expect(levelGapOf(1.3)).toEqual({ kind: 'above', gap: 1.3 });
  });

  it('is the same level when it rounds to 0,00 — either way', () => {
    expect(levelGapOf(0)).toEqual({ kind: 'same' });
    expect(levelGapOf(0.004)).toEqual({ kind: 'same' });
    expect(levelGapOf(-0.004)).toEqual({ kind: 'same' });
  });

  it('reads a float the wire carried as the hundredth it was', () => {
    // 2,71 − 2,69 in binary is 0,019999…: still two hundredths.
    expect(levelGapOf(2.69 - 2.71)).toEqual({ kind: 'below', gap: 0.02 });
  });
});

describe('moreSportsOf — N sports › (the mechanics §6.3)', () => {
  it('counts every shared sport, and says nothing with one', () => {
    expect(moreSportsOf(zofia([PADEL, SQUASH]))).toBe(2);
    expect(moreSportsOf(zofia([PADEL]))).toBeUndefined();
  });
});

describe('foundAtSameLevel — where a request from the row was found (the mechanics §12)', () => {
  it('names the card’s sport, the one the other person’s line compares', () => {
    expect(foundAtSameLevel('squash')).toEqual({ from: 'SAME_LEVEL', sport: 'squash' });
  });
});
