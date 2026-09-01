/**
 * The ladder's three shapes, and the two empties the wire deliberately keeps apart.
 *
 * What is asserted here is mostly what the pool must **not** draw: a control priced at nobody,
 * and a screen with nothing on it at all — which is the one answer that is never honest. And
 * one thing it must **not** take away, which is the mistake this file was written with: a
 * clamped answer's radius rungs are real, and deleting them on the bit takes a true one-tap
 * widening off exactly the screen it was built for.
 */

import type { RungOffer } from './candidate';

import { poolLadder } from './poolLadder';

const times = (above: number): RungOffer => ({
  rung: 'A',
  ask: 'TIMES',
  candidatesAboveFloor: above,
  window: 'THIS_WEEK',
});

const radius = (above: number, radiusKm = 22): RungOffer => ({
  rung: 'B',
  ask: 'RADIUS',
  candidatesAboveFloor: above,
  window: 'THIS_WEEK',
  radiusKm,
});

describe('a list nobody needed offers for', () => {
  it('draws no ladder at all — the list is the answer', () => {
    expect(poolLadder({ rows: 9, offers: null })).toEqual({ kind: 'silent' });
  });

  /**
   * `null` says the offers were never computed *because the list cleared five*. Arriving with
   * no rows contradicts that, and the honest answer to a contradiction is the sentence rather
   * than a blank screen.
   */
  it('states the terminal sentence when it contradicts itself', () => {
    expect(poolLadder({ rows: 0, offers: null })).toEqual({
      kind: 'exhausted',
    });
  });
});

describe('offers that are worth taking', () => {
  it('draws each priced rung as a control, in the order the engine recommended', () => {
    const offers = [times(7), radius(9)];

    expect(poolLadder({ rows: 2, offers })).toEqual({
      kind: 'offered',
      controls: offers,
      statements: [],
    });
  });
});

describe('a rung priced at nobody', () => {
  /**
   * ADR-0099 §5 prints the count on the button; this is its one narrow amendment. A button
   * that provably returns an empty list is a control lying about being useful, and the count
   * is still said — as a sentence rather than as a tap.
   */
  it('is a statement and never a control', () => {
    const empty = radius(0, 32);

    expect(poolLadder({ rows: 0, offers: [empty, times(4)] })).toEqual({
      kind: 'offered',
      controls: [times(4)],
      statements: [empty],
    });
  });

  it('leaves nothing behind when every offer is priced at nobody', () => {
    expect(poolLadder({ rows: 0, offers: [radius(0), times(0)] })).toEqual({
      kind: 'offered',
      controls: [],
      statements: [radius(0), times(0)],
    });
  });
});

describe('the clamp', () => {
  /**
   * The bit says *a widening offer hit the slider's ceiling*, **not** *the searcher is at the
   * ceiling*. `radius_ladder` sets it whenever a multiplier overshoots and then clamps that
   * rung down to 50 km and offers it anyway, so a searcher at 26 km gets 39 and 50 with the
   * bit set — and both are priced by a genuine re-run. Reading the bit as a gate would take a
   * true one-tap widening away from exactly the player the ladder was built for.
   */
  it('is not read here at all, so a clamped answer keeps every rung it was offered', () => {
    const offers = [radius(9, 50), times(7)];

    expect(poolLadder({ rows: 0, offers })).toEqual({
      kind: 'offered',
      controls: offers,
      statements: [],
    });
  });

  /**
   * The searcher already at the maximum — `RadiusLadder`'s *"clamped is recorded even when it
   * left no rung standing"*. There is nothing to filter, because the engine offered nothing,
   * and what the bit decides is which terminal sentence `terminalReachLine` writes.
   */
  it('leaves the terminal shape where the ceiling really did leave no rung', () => {
    expect(poolLadder({ rows: 0, offers: [] })).toEqual({ kind: 'exhausted' });
  });
});

describe('a list with nothing left to offer', () => {
  it('is the terminal sentence, with whatever rows there are above it', () => {
    expect(poolLadder({ rows: 3, offers: [] })).toEqual({ kind: 'exhausted' });
    expect(poolLadder({ rows: 0, offers: [] })).toEqual({ kind: 'exhausted' });
  });
});
