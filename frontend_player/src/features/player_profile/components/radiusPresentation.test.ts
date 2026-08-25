/**
 * The figure and the plain words, which are one fact rendered twice.
 *
 * The words are the assertion worth having. A number in kilometres means nothing to a
 * player who does not think in kilometres, and the whole reason the line exists is that
 * *12* and *40* are different kinds of decision rather than different numbers — so what is
 * pinned here is that the bands change where the decision changes, and that the reading
 * holds at distances no served bound produces today.
 */

import { radiusFigure, radiusWords, spokenRadius, widestRadiusFigure } from './radiusPresentation';

describe('the figure', () => {
  it('carries its unit, so a bare number is never on screen alone', () => {
    expect(radiusFigure(1)).toBe('1 km');
    expect(radiusFigure(50)).toBe('50 km');
  });

  /**
   * The box reserves the widest figure the served maximum can produce, so dragging from 9
   * to 10 does not move the text under the finger that is moving it.
   */
  it('reserves the width of the largest value the bounds can reach', () => {
    expect(widestRadiusFigure({ minimumKm: 1, maximumKm: 50, stepKm: 1, defaultKm: 10 })).toBe(
      '50 km',
    );
    // The last value on a step, not the served maximum: 2 + 5n reaches 17 and then 22.
    expect(widestRadiusFigure({ minimumKm: 2, maximumKm: 21, stepKm: 5, defaultKm: 7 })).toBe(
      '17 km',
    );
  });
});

describe('the plain-word reading', () => {
  it('changes where the decision changes rather than every kilometre', () => {
    expect(radiusWords(1)).toBe('Just your own neighbourhood');
    expect(radiusWords(2)).toBe('Just your own neighbourhood');
    expect(radiusWords(3)).toBe('A short ride away');
    expect(radiusWords(5)).toBe('A short ride away');
    expect(radiusWords(6)).toBe('Across your town');
    expect(radiusWords(15)).toBe('Across your town');
    expect(radiusWords(16)).toBe('Your town and the ones around it');
    expect(radiusWords(30)).toBe('Your town and the ones around it');
    expect(radiusWords(31)).toBe('A long drive out');
  });

  /**
   * The bounds are product's and may be retuned without a client release, so the reading
   * is a function of a distance rather than of a range. A radius past anything served
   * today still reads as something.
   */
  it('reads a distance no served bound produces today', () => {
    expect(radiusWords(500)).toBe('A long drive out');
  });
});

describe('what a screen reader is told', () => {
  /**
   * One announcement, not two. The figure and the words are the same fact drawn twice for
   * whoever is looking; read as two values they would say the control has two.
   */
  it('says the figure and the words as one value', () => {
    expect(spokenRadius(12)).toBe('12 kilometres, across your town');
  });

  /** The unit is spelled out: `km` is read as two letters by some screen readers. */
  it('spells the unit, and says one kilometre in the singular', () => {
    expect(spokenRadius(1)).toBe('1 kilometre, just your own neighbourhood');
  });
});
