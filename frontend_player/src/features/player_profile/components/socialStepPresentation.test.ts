import { SOCIAL_STEPS } from '../domain/socialSteps';

import { stepCopy, stepEyebrow } from './socialStepPresentation';

describe('the eyebrow of a social step', () => {
  it('says the player is still setting up, and where they are in it', () => {
    // Story 12: a player should know these screens end. The count is the only thing that
    // says so, and unlike part one it can be honest about the total — the part is six
    // steps whatever the player answers.
    expect(stepEyebrow('tags')).toBe('Setting up · Step 1 of 6');
    expect(stepEyebrow('location')).toBe('Setting up · Step 5 of 6');
    // Total for every step, including the last, which carries the finish and still says
    // where it is — six of six is the honest way to say nothing is left after it.
    expect(stepEyebrow('gender')).toBe('Setting up · Step 6 of 6');
  });
});

describe('what each step says it is for', () => {
  it('gives every step a title and one line about the decision it asks for', () => {
    // One decision per screen (story 13), so every step has exactly one sentence about
    // what it wants — and a step added without copy fails here rather than shipping blank.
    for (const step of SOCIAL_STEPS) {
      const copy = stepCopy(step);
      expect(copy.title.length).toBeGreaterThan(0);
      expect(copy.asks.length).toBeGreaterThan(0);
    }
  });
});
