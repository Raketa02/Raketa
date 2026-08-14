import { onboardingKeys } from './onboardingKeys';

describe('query keys', () => {
  it('nests every key under the feature root, so a sign-out clears them together', () => {
    expect(onboardingKeys.ratings()).toEqual(['onboarding', 'ratings']);
    expect(onboardingKeys.runInProgress()).toEqual(['onboarding', 'run-in-progress']);
    expect(onboardingKeys.sports()).toEqual(['onboarding', 'sports']);
  });

  it('keys an assessment by its id', () => {
    // Every parameter that changes the response is in the key. Two assessments sharing
    // one key is two players' transcripts in one cache entry.
    expect(onboardingKeys.assessment('abc')).toEqual(['onboarding', 'assessment', 'abc']);
    expect(onboardingKeys.assessment('abc')).not.toEqual(onboardingKeys.assessment('xyz'));
  });
});
