/**
 * A term that stood down.
 *
 * Three rules are asserted rather than the wording. The sentence is `(term, reason)` and not
 * either alone; the platform's own gap is stated **once, in a footer**, never per row; and the
 * reliability line says nothing about *when*, which is where ADR-0106 §5's recency refusal
 * would otherwise leak back in as copy.
 */

import { DEGRADED_REASONS, TERMS } from '../domain/vocabulary';

import { NOT_ON_THIS_PLATFORM_FOOTER, degradedLine } from './degradedPresentation';

describe('one code, two sentences', () => {
  it('says whose gap it is, per term', () => {
    expect(degradedLine('AVAILABILITY_OVERLAP', 'NOTHING_FROM_YOU')).toBe('Your week is blank');
    expect(degradedLine('AVAILABILITY_OVERLAP', 'NOTHING_FROM_THEM')).toBe('Their week is blank');
  });

  it('gives one code two readings across two terms', () => {
    // #233 §8: `INTENT_ALIGNMENT + NOTHING_FROM_THEM` and `SOCIAL_VIBE + NOTHING_FROM_THEM`
    // are two different sentences from one code.
    expect(degradedLine('INTENT_ALIGNMENT', 'NOTHING_FROM_THEM')).not.toBe(
      degradedLine('SOCIAL_VIBE', 'NOTHING_FROM_THEM'),
    );
  });

  it('says nothing for the two terms that never stand down', () => {
    for (const reason of DEGRADED_REASONS) {
      expect(degradedLine('LEVEL_FIT', reason)).toBeUndefined();
      expect(degradedLine('DISTANCE', reason)).toBeUndefined();
    }
  });

  it('has no sentence for your own record, because the term reads theirs', () => {
    expect(degradedLine('RELIABILITY', 'NOTHING_FROM_YOU')).toBeUndefined();
    expect(degradedLine('RELIABILITY', 'NOTHING_FROM_THEM')).toBe('Nothing on their record yet');
  });
});

/**
 * **The fourth reason is the surface's, and it names nobody's gap** (ADR-0169 §2). The deck
 * deals everybody under one ruler and reads no declaration, so the intent term stands down on
 * every card there — filing that under either person's code would print a sentence about a
 * person that is false of them.
 */
describe('a term the surface declined to read', () => {
  it('says the term is not read here, and blames neither of you', () => {
    const line = degradedLine('INTENT_ALIGNMENT', 'NOT_READ_ON_THIS_SURFACE') ?? '';

    expect(line).toMatch(/isn't read here/);
    expect(line).not.toMatch(/haven't|hasn't|they |their /i);
  });

  it('is a different sentence from either person’s gap on the same term', () => {
    expect(degradedLine('INTENT_ALIGNMENT', 'NOT_READ_ON_THIS_SURFACE')).not.toBe(
      degradedLine('INTENT_ALIGNMENT', 'NOTHING_FROM_THEM'),
    );
    expect(degradedLine('INTENT_ALIGNMENT', 'NOT_READ_ON_THIS_SURFACE')).not.toBe(
      degradedLine('INTENT_ALIGNMENT', 'NOTHING_FROM_YOU'),
    );
  });

  it('has no sentence for a term no surface stands down this way', () => {
    // Only the intent term is stood down by a surface today; the rest keep the gap in place
    // rather than borrow a sentence written about somebody.
    expect(degradedLine('RELIABILITY', 'NOT_READ_ON_THIS_SURFACE')).toBeUndefined();
    expect(degradedLine('SOCIAL_VIBE', 'NOT_READ_ON_THIS_SURFACE')).toBeUndefined();
  });
});

describe('the platform’s own gap', () => {
  it('is a footer and never a line on a row', () => {
    // Two tiers: otherwise reliability's line prints identically on twenty cards and reads as
    // twenty separate shortfalls.
    for (const term of TERMS) {
      expect(degradedLine(term, 'NOT_YET_ON_THIS_PLATFORM')).toBeUndefined();
    }

    expect(NOT_ON_THIS_PLATFORM_FOOTER).toMatch(/isn't counted for anybody/);
  });
});

describe('the wording that must not drift', () => {
  it('dates nobody', () => {
    // The code swallows three causes so that the day reliability goes live the sheet still
    // cannot date anybody: *nothing on their record yet*, never *not recently*.
    const line = degradedLine('RELIABILITY', 'NOTHING_FROM_THEM') ?? '';

    expect(line).not.toMatch(/recent|lately|last|month|week|day/i);
  });

  it('says a blank week is blank, never that somebody is unavailable', () => {
    // The same reading ADR-0102 withdrew on the profile step, met here from the other side.
    for (const reason of ['NOTHING_FROM_YOU', 'NOTHING_FROM_THEM'] as const) {
      expect(degradedLine('AVAILABILITY_OVERLAP', reason)).not.toMatch(/unavailable|never free/i);
    }
  });
});
