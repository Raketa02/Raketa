/**
 * The shorter value, and the two edges that decide whether there is one.
 *
 * The rule reads no meaning out of a place — it cuts at the first comma and never claims the tail
 * was a court — so what is asserted here is that it cuts where there is something to cut and
 * leaves the value alone where there is not.
 */

import { placeWithoutTheCourt } from './placeName';

it('drops everything after the first comma', () => {
  expect(placeWithoutTheCourt('Zabłocie Sport, court 3')).toBe('Zabłocie Sport');
  expect(placeWithoutTheCourt('Zabłocie Sport, court 3, by the bar')).toBe('Zabłocie Sport');
});

it('draws a place with no comma in it whole', () => {
  expect(placeWithoutTheCourt('Zabłocie Sport')).toBe('Zabłocie Sport');
});

/** Nothing before the comma is nothing to shorten to, and a blank chip says less than a long one. */
it('keeps the value where the cut would leave nothing', () => {
  expect(placeWithoutTheCourt(', court 3')).toBe(', court 3');
});
