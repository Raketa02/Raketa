/**
 * The words on the tags step, without a renderer.
 *
 * The labels are copy and copy changes; what these hold is the two things that must not.
 * Every id this build can draw has words, and no two ids share the same ones — two chips
 * reading alike are two choices a player cannot tell apart.
 */

import { SOCIAL_TAG_GROUP_IDS, SOCIAL_TAG_IDS } from '../domain/SocialTag';

import {
  socialTagCeilingTitle,
  socialTagGroupHeading,
  socialTagLabel,
  socialTagsContinueLabel,
  socialTagsEyebrow,
} from './socialTagPresentation';

describe('what a tag is called', () => {
  it('gives every id this build can draw its own words', () => {
    // A tag added without copy fails here rather than shipping as a chip with nothing on it.
    const labels = SOCIAL_TAG_IDS.map(socialTagLabel);

    expect(labels.every((label) => label.length > 0)).toBe(true);
    expect(new Set(labels).size).toBe(SOCIAL_TAG_IDS.length);
  });

  it('gives every group a heading naming what it is about', () => {
    const headings = SOCIAL_TAG_GROUP_IDS.map(socialTagGroupHeading);

    expect(headings).toEqual(['After the match', 'On the court', "Why you're here"]);
  });
});

describe('the eyebrow', () => {
  it('carries the served rule alongside the position', () => {
    // Story 18: the floor is learned by reading the screen rather than by being stopped.
    expect(socialTagsEyebrow({ minimum: 2, maximum: 6 })).toBe(
      'Setting up · Step 1 of 6 · Pick 2 to 6',
    );
  });

  it('quotes the numbers that were served, not the ones this build expects', () => {
    expect(socialTagsEyebrow({ minimum: 3, maximum: 5 })).toBe(
      'Setting up · Step 1 of 6 · Pick 3 to 5',
    );
  });

  it('states the position alone until the bounds have arrived', () => {
    // A range with a blank in it is a rule stated wrong, which is worse than a rule not yet
    // stated — and the chips it governs are not on screen yet either.
    expect(socialTagsEyebrow(undefined)).toBe('Setting up · Step 1 of 6');
  });
});

describe('the continue control', () => {
  it('says how many more are needed, counting down', () => {
    // Story 17: a disabled button is never a mystery.
    expect(socialTagsContinueLabel({ kind: 'short', missing: 2 })).toBe('Pick 2 tags to continue');
    expect(socialTagsContinueLabel({ kind: 'short', missing: 1 })).toBe(
      'Pick 1 more tag to continue',
    );
  });

  it('is just the move once the floor is met', () => {
    expect(socialTagsContinueLabel({ kind: 'ready' })).toBe('Continue');
  });
});

describe('the ceiling title', () => {
  it('names the served ceiling', () => {
    expect(socialTagCeilingTitle({ minimum: 2, maximum: 6 })).toBe('6 tags is the most');
    expect(socialTagCeilingTitle({ minimum: 2, maximum: 4 })).toBe('4 tags is the most');
  });
});
