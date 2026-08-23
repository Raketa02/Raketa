/**
 * The two guards a `Record` cannot carry for the sport bar.
 *
 * Completeness is a typecheck (`ADR-0075`) — a fifth sport added to the contract
 * without a chip fails to compile. What it cannot see is **order**, which a
 * `Record` has none of and which both UI authorities fix, and it cannot see the two
 * lists drifting apart.
 */

import { DEFAULT_SPORT_FILTER, SPORT_BAR, SPORT_CHIP_COPY } from './sportBar';
import type { AssertTrue, IsClosedUnion, SportFilter } from './codes';

/** Fails `pnpm typecheck` the day `SportFilter` widens to a bare string. */
export type SportFilterKeyIsClosed = AssertTrue<IsClosedUnion<SportFilter>>;

describe('the bar', () => {
  it('is five chips in the authorities’ order', () => {
    expect(SPORT_BAR).toEqual(['all', 'PADEL', 'TENNIS', 'SQUASH', 'BADMINTON']);
  });

  it('and the copy table cover exactly each other', () => {
    // The list is written out separately because a `Record` cannot hold an order, so
    // the two can drift — and a sixth chip in one and not the other ships a sport
    // nobody can filter to, or a chip that filters to nothing.
    expect([...SPORT_BAR].sort()).toEqual(Object.keys(SPORT_CHIP_COPY).sort());
  });

  it('starts at All, on every visit', () => {
    expect(DEFAULT_SPORT_FILTER).toBe('all');
    expect(SPORT_BAR[0]).toBe(DEFAULT_SPORT_FILTER);
  });
});

describe('a chip', () => {
  it('says a word, never a blank', () => {
    for (const [value, chip] of Object.entries(SPORT_CHIP_COPY)) {
      expect(chip.label.trim()).not.toBe('');
      expect(chip.label).not.toBe(value);
    }
  });

  it('wears a swatch on the four sports and none on All', () => {
    // `All` is not a sport, which is the distinction the whole bar is carrying.
    expect(SPORT_CHIP_COPY.all.swatch).toBeUndefined();

    const sports = SPORT_BAR.filter((value) => value !== 'all');
    expect(sports.map((value) => SPORT_CHIP_COPY[value].swatch)).toEqual([
      'padel',
      'tennis',
      'squash',
      'badminton',
    ]);
  });

  it('keeps the sport registry’s own spelling for the four', () => {
    // One name for one sport: the client sends back the value it already holds,
    // rather than a second, lower-cased vocabulary for the same four things.
    for (const value of SPORT_BAR) {
      if (value === 'all') continue;
      expect(value).toBe(value.toUpperCase());
    }
  });
});
