/**
 * The balance word, and the two places it is the whole of Part 13's compliance.
 *
 * Three rules are asserted. **Every percentage has a word**, because the bar is a colour and
 * a figure tinted with nothing beside it is colour as the only cue. **The word breaks in four
 * where the tone breaks in three**, which is recorded rather than tidied. And the bar's
 * accessible name is the word *and* the figure, never one of them.
 */

import { balanceLabel, balanceTone, balanceWord } from './balancePresentation';

describe('the balance word', () => {
  it('breaks at 85, 70 and 55', () => {
    expect(balanceWord(100)).toBe('Very even');
    expect(balanceWord(85)).toBe('Very even');
    expect(balanceWord(84)).toBe('Fairly even');
    expect(balanceWord(70)).toBe('Fairly even');
    expect(balanceWord(69)).toBe('One side favoured');
    expect(balanceWord(55)).toBe('One side favoured');
    expect(balanceWord(54)).toBe('Lopsided');
    expect(balanceWord(0)).toBe('Lopsided');
  });

  it('gives every percentage a word, because the tone is not allowed to be the only cue', () => {
    for (let pct = 0; pct <= 100; pct += 1) expect(balanceWord(pct)).not.toBe('');
  });
});

describe('the tone beside it', () => {
  it('breaks at 70 and 55, one step coarser than the word', () => {
    expect(balanceTone(85)).toBe('ok');
    expect(balanceTone(70)).toBe('ok');
    expect(balanceTone(69)).toBe('warn');
    expect(balanceTone(55)).toBe('warn');
    expect(balanceTone(54)).toBe('bad');
  });

  it('lets Very even and Fairly even share one green', () => {
    // Recorded rather than fixed (7.11): Part 13 is satisfied by the word, and a fourth tone
    // would need a fourth MEANING, which 15.2 forbids inventing.
    expect(balanceWord(91)).not.toBe(balanceWord(74));
    expect(balanceTone(91)).toBe(balanceTone(74));
  });
});

describe("the bar's accessible name", () => {
  it('is the word and its figure, in that order — the word is the point', () => {
    expect(balanceLabel(74)).toBe('Fairly even, 74%');
  });

  it('rounds the figure the one way this app rounds a percentage', () => {
    expect(balanceLabel(73.6)).toBe('Fairly even, 74%');
  });

  it('never announces a bare number', () => {
    for (const pct of [0, 54, 55, 69, 70, 84, 85, 100]) {
      expect(balanceLabel(pct)).toMatch(/^[A-Z][a-z]/);
    }
  });
});
