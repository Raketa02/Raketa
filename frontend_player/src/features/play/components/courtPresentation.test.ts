/**
 * An empty seat, and why this four.
 *
 * Two rules are asserted. **`NO_SHARED_SLOTS` is a dock and not a refusal** — nobody is
 * removed from the court for it, and the sentence must not read as though somebody were. And
 * **no group reason quotes a figure**: `G` is recorded and never returned, so these five
 * sentences are the whole explanation and a number in one would be invented.
 */

import { GROUP_REASONS, UNFILLED_REASONS } from '../domain/vocabulary';

import { WITHHELD_SEAT_LINE, groupReasonLine, unfilledSeatLine } from './courtPresentation';

describe('an unfilled seat', () => {
  it('gives each obstacle its own sentence', () => {
    const lines = UNFILLED_REASONS.map(unfilledSeatLine);

    expect(new Set(lines).size).toBe(UNFILLED_REASONS.length);
  });

  it('states the shortfall rather than a count of who was found', () => {
    // #223 replaced AC-69's "Only found N" with the actual obstacle for the actual seat.
    for (const line of UNFILLED_REASONS.map(unfilledSeatLine)) {
      expect(line).not.toMatch(/^Only found/);
    }
  });

  it('reads a shared-slot zero as a bend, never as a removal', () => {
    const line = unfilledSeatLine('NO_SHARED_SLOTS');

    expect(line).toMatch(/bend/);
    expect(line).not.toMatch(/cannot|can't|unavailable|removed/i);
  });
});

describe('why this four', () => {
  it('gives each of the five its own sentence', () => {
    const lines = GROUP_REASONS.map(groupReasonLine);

    expect(new Set(lines).size).toBe(GROUP_REASONS.length);
  });

  it('quotes no figure, because the objective is recorded and never returned', () => {
    for (const line of GROUP_REASONS.map(groupReasonLine)) expect(line).not.toMatch(/\d/);
  });

  it('gives the two group rapport terms one sentence', () => {
    // The code is the vocabulary: splitting it in copy would publish a distinction the enum
    // deliberately does not carry.
    expect(groupReasonLine('GROUP_RAPPORT')).toBe('These four read each other well');
  });
});

describe('a seat whose player is no longer available', () => {
  it('states the fact and never the cause', () => {
    // Four fail-closed gates reach this mark — a block either way, a hold, an account that
    // may not be shown, and the mutual gender preference — and naming which one fired would
    // tell a searcher that a particular person blocked them or changed a safety setting.
    const said = WITHHELD_SEAT_LINE.toLowerCase();

    for (const cause of ['block', 'hold', 'suspend', 'preference', 'gender']) {
      expect(said).not.toContain(cause);
    }
  });

  it('says something changed rather than something about them', () => {
    // The register the send refusal is held to: the fact is that the line-up went out of
    // date, and a person's standing is not the organiser's to be told.
    expect(WITHHELD_SEAT_LINE).toMatch(/^Something's changed/);
  });

  it('is not a sentence about an unfilled seat — the seat is filled, by somebody', () => {
    expect(UNFILLED_REASONS.map(unfilledSeatLine)).not.toContain(WITHHELD_SEAT_LINE);
  });
});
