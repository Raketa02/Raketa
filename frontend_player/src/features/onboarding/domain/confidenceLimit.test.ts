import { confidenceLimit } from './confidenceLimit';

/**
 * The ceiling the engine serves today. A literal *in the test*, deliberately: what the rule
 * must not have is a copy in the bundle, and a test that fed it its own constant on both
 * sides would pass whatever the rule compared.
 */
const CEILING = 30;

describe('what held a Confidence where it is', () => {
  it('is the ceiling for a rating that reached it', () => {
    expect(confidenceLimit(CEILING, CEILING)).toBe('ceiling');
  });

  it('is the evidence for a rating that did not', () => {
    expect(confidenceLimit(CEILING - 1, CEILING)).toBe('evidence');
  });

  it('is the ceiling for anything above it, never the evidence', () => {
    // Onboarding cannot produce this and a rating that did would be the engine
    // contradicting the glossary — but "the evidence limited you" is the one sentence
    // that cannot be true of it, so the rule may not fall through to it.
    expect(confidenceLimit(CEILING + 45, CEILING)).toBe('ceiling');
  });

  it('reads the ceiling it was given rather than a number of its own', () => {
    // The pair either side of the boundary, so what is pinned is the boundary and not a
    // literal's spelling.
    expect(confidenceLimit(CEILING - 0.5, CEILING)).toBe('evidence');
    expect(confidenceLimit(CEILING + 0.5, CEILING)).toBe('ceiling');
  });

  it('moves the boundary when the engine retunes it, with nothing here to update', () => {
    // The whole point of the ceiling being served: a rating produced by an engine whose
    // ceiling is 45 and whose Confidence reached 40 was held by its *evidence*, and a
    // client holding 30 would tell that player the ceiling stopped them. Both numbers come
    // from the same response, so the two can never be a version apart.
    expect(confidenceLimit(40, 45)).toBe('evidence');
    expect(confidenceLimit(45, 45)).toBe('ceiling');

    // And the same Confidence against a lower ceiling is the other answer entirely.
    expect(confidenceLimit(40, 40)).toBe('ceiling');
  });

  it('says the evidence for a beginner, who has no widener at all', () => {
    // The case that rules out reading the wideners instead: one answer, nothing widened,
    // and a Confidence nowhere near the ceiling. Thin evidence is the absence of
    // evidence, not a widener, and telling this player the ceiling was their limit would
    // be the wrong sentence about the only thing the app knows about them.
    expect(confidenceLimit(9, CEILING)).toBe('evidence');
  });
});
