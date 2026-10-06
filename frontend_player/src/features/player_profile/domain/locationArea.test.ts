/**
 * The coarsening, which is the whole of what this app is allowed to remember about where a
 * player is.
 *
 * The assertions that matter are the ones about what *cannot* be got back out: two fixes a
 * hundred metres apart have to land on the same area, or the rounding is decoration over a
 * precise position that is still there.
 */

import { areaAround, sameArea, LOCATION_AREA_DECIMALS } from './locationArea';

describe('the area a fix falls in', () => {
  it('keeps two decimal places, which is the resolution distances are expressed in', () => {
    expect(areaAround(41.3874, 2.1686)).toEqual({ latitude: 41.39, longitude: 2.17 });
    expect(LOCATION_AREA_DECIMALS).toBe(2);
  });

  /**
   * The point of the whole module. A device reports metres; an area is about a kilometre
   * across, so several readings from the same neighbourhood are one answer and the reading
   * that produced it cannot be recovered from what was kept.
   */
  it('cannot tell two fixes a hundred metres apart apart', () => {
    const one = areaAround(41.3874, 2.1686);
    const other = areaAround(41.3881, 2.1692);

    expect(one).toEqual(other);
  });

  it('coarsens a southern, western fix the same way', () => {
    expect(areaAround(-34.6037, -58.3816)).toEqual({ latitude: -34.6, longitude: -58.38 });
  });

  /**
   * Re-coarsening is a no-op, which is what lets the same rule run in more than one place
   * without the second run moving the answer: the backend rounds again on the way in
   * (`player_profile/domain/location.py`), and the draft holds what it will send.
   */
  it('leaves an already-coarse pair exactly where it is', () => {
    const area = areaAround(41.3874, 2.1686);

    expect(areaAround(area.latitude, area.longitude)).toEqual(area);
  });

  it('holds a fix that is already on the grid without inventing a difference', () => {
    expect(areaAround(41, 2)).toEqual({ latitude: 41, longitude: 2 });
  });
});

describe('two areas being the same place', () => {
  it('is true for the same pair however it was reached', () => {
    expect(sameArea(areaAround(41.3874, 2.1686), areaAround(41.3881, 2.1692))).toBe(true);
  });

  it('is false one grid square away', () => {
    expect(
      sameArea({ latitude: 41.39, longitude: 2.17 }, { latitude: 41.4, longitude: 2.17 }),
    ).toBe(false);
  });

  /** An area and no area are different answers — a player who has said where is not one who has not. */
  it('is false when only one side has an area', () => {
    expect(sameArea(undefined, { latitude: 41.39, longitude: 2.17 })).toBe(false);
    expect(sameArea({ latitude: 41.39, longitude: 2.17 }, undefined)).toBe(false);
  });

  /** Both sides unanswered is the same answer, so a re-read that found nothing records nothing. */
  it('is true when neither side has one', () => {
    expect(sameArea(undefined, undefined)).toBe(true);
  });
});
