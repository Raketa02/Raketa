import { ONBOARDING_CONFIDENCE_CEILING } from './AssessmentResult';
import { confidenceLimit } from './confidenceLimit';

describe('what held a Confidence where it is', () => {
  it('is the ceiling for a rating that reached it', () => {
    expect(confidenceLimit(ONBOARDING_CONFIDENCE_CEILING)).toBe('ceiling');
  });

  it('is the evidence for a rating that did not', () => {
    expect(confidenceLimit(ONBOARDING_CONFIDENCE_CEILING - 1)).toBe('evidence');
  });

  it('is the ceiling for anything above it, never the evidence', () => {
    // Onboarding cannot produce this and a rating that did would be the engine
    // contradicting the glossary — but "the evidence limited you" is the one sentence
    // that cannot be true of it, so the rule may not fall through to it.
    expect(confidenceLimit(ONBOARDING_CONFIDENCE_CEILING + 45)).toBe('ceiling');
  });

  it('reads the ceiling rather than a number of its own', () => {
    // The pair either side of the constant, so what is pinned is the boundary and not the
    // literal's spelling. Moving the ceiling moves both.
    expect(confidenceLimit(ONBOARDING_CONFIDENCE_CEILING - 0.5)).toBe('evidence');
    expect(confidenceLimit(ONBOARDING_CONFIDENCE_CEILING + 0.5)).toBe('ceiling');
  });

  it('says the evidence for a beginner, who has no widener at all', () => {
    // The case that rules out reading the wideners instead: one answer, nothing widened,
    // and a Confidence nowhere near the ceiling. Thin evidence is the absence of
    // evidence, not a widener, and telling this player the ceiling was their limit would
    // be the wrong sentence about the only thing the app knows about them.
    expect(confidenceLimit(9)).toBe('evidence');
  });
});
