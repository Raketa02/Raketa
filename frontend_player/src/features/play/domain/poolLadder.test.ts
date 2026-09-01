/**
 * The ladder's three shapes, and the two empties the wire deliberately keeps apart.
 *
 * What is asserted here is mostly what the pool must **not** draw: a control priced at nobody,
 * a *widen* offered to a player already at their ceiling, and a screen with nothing on it at
 * all — which is the one answer that is never honest.
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
    expect(poolLadder({ rows: 9, offers: null, radiusClamp: false })).toEqual({ kind: 'silent' });
  });

  /**
   * `null` says the offers were never computed *because the list cleared five*. Arriving with
   * no rows contradicts that, and the honest answer to a contradiction is the sentence rather
   * than a blank screen.
   */
  it('states the terminal sentence when it contradicts itself', () => {
    expect(poolLadder({ rows: 0, offers: null, radiusClamp: false })).toEqual({
      kind: 'exhausted',
    });
  });
});

describe('offers that are worth taking', () => {
  it('draws each priced rung as a control, in the order the engine recommended', () => {
    const offers = [times(7), radius(9)];

    expect(poolLadder({ rows: 2, offers, radiusClamp: false })).toEqual({
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

    expect(poolLadder({ rows: 0, offers: [empty, times(4)], radiusClamp: false })).toEqual({
      kind: 'offered',
      controls: [times(4)],
      statements: [empty],
    });
  });

  it('leaves nothing behind when every offer is priced at nobody', () => {
    expect(poolLadder({ rows: 0, offers: [radius(0), times(0)], radiusClamp: false })).toEqual({
      kind: 'offered',
      controls: [],
      statements: [radius(0), times(0)],
    });
  });
});

describe('the clamp', () => {
  /**
   * The bit is true when the slider's own ceiling bit at all, and every *widen* sentence is
   * addressed to a player who may have nothing left to widen. Asking somebody for something
   * they cannot give is the one thing the ladder must not do.
   */
  it('takes every radius rung away, control or statement', () => {
    expect(poolLadder({ rows: 0, offers: [radius(9), times(7)], radiusClamp: true })).toEqual({
      kind: 'offered',
      controls: [times(7)],
      statements: [],
    });
  });

  it('leaves the terminal sentence when the radius was the only ask left', () => {
    expect(poolLadder({ rows: 0, offers: [radius(9)], radiusClamp: true })).toEqual({
      kind: 'exhausted',
    });
  });
});

describe('a list with nothing left to offer', () => {
  it('is the terminal sentence, with whatever rows there are above it', () => {
    expect(poolLadder({ rows: 3, offers: [], radiusClamp: false })).toEqual({ kind: 'exhausted' });
    expect(poolLadder({ rows: 0, offers: [], radiusClamp: false })).toEqual({ kind: 'exhausted' });
  });
});
