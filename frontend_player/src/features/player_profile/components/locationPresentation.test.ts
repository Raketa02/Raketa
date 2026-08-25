/**
 * How an area is written, and how it is read out.
 *
 * The figures are the assertion worth having: an area is written to exactly two decimal
 * places whatever the number, because a place that printed as `41,4` and a place that
 * printed as `41,39` would look like two different kinds of answer when they are the same
 * kind — and because the second decimal is where *about a kilometre* is visible at all.
 */

import {
  WITHOUT_AN_AREA_LABEL,
  WITH_AN_AREA_LABEL,
  areaLine,
  continueLabel,
  spokenArea,
} from './locationPresentation';

describe('an area, written', () => {
  it('names both hemispheres it is in', () => {
    expect(areaLine({ latitude: 41.39, longitude: 2.17 })).toBe('41,39° N · 2,17° E');
    expect(areaLine({ latitude: -34.6, longitude: -58.38 })).toBe('34,60° S · 58,38° W');
  });

  /** Comma decimals, two places — the house convention every figure in this app follows. */
  it('always shows both decimals, so two areas are the same shape of answer', () => {
    expect(areaLine({ latitude: 41.4, longitude: 2 })).toBe('41,40° N · 2,00° E');
  });

  /** The equator and the meridian are north and east of nothing, and a sign would say otherwise. */
  it('reads zero as north and east rather than as a sign', () => {
    expect(areaLine({ latitude: 0, longitude: 0 })).toBe('0,00° N · 0,00° E');
  });
});

describe('an area, read out', () => {
  /**
   * The degree mark and the middle dot are decoration to a screen reader — one is announced
   * as "degrees" by some and skipped by others, and the dot is silence. The spoken form
   * says the words instead.
   */
  it('says the words the symbols stand for', () => {
    expect(spokenArea({ latitude: 41.39, longitude: 2.17 })).toBe(
      'Your area: 41,39 degrees north, 2,17 degrees east',
    );
    expect(spokenArea({ latitude: -34.6, longitude: -58.38 })).toBe(
      'Your area: 34,60 degrees south, 58,38 degrees west',
    );
  });
});

describe('the control that continues', () => {
  /**
   * The label names the consequence rather than hiding it behind a note the player may not
   * read. Location is what discovery is built on: leaving without one is allowed, and it is
   * not the same act as leaving with one.
   */
  it('says what continuing costs when there is no area', () => {
    expect(continueLabel(undefined)).toBe(WITHOUT_AN_AREA_LABEL);
    expect(continueLabel({ latitude: 41.39, longitude: 2.17 })).toBe(WITH_AN_AREA_LABEL);
  });
});
