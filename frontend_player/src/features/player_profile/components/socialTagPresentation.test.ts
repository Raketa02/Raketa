/**
 * The words the tags **step** says, without a renderer — the rule it states and the ceiling
 * it refuses at, both quoting numbers the server served rather than numbers this build
 * expects.
 *
 * What a tag is *called* is asserted beside the promoted table, in
 * `@/shared/vocabulary/socialTagPresentation`.
 */

import {
  socialTagCeilingTitle,
  socialTagsContinueLabel,
  socialTagsEyebrow,
  socialTagsRule,
  socialTagsSaveLabel,
} from './socialTagPresentation';

describe('the eyebrow', () => {
  it('carries the served rule alongside the position', () => {
    // Story 18: the floor is learned by reading the screen rather than by being stopped.
    // What the platform serves since ADR-0207 §7.
    expect(socialTagsEyebrow({ minimum: 2, maximum: 8 })).toBe(
      'Setting up · Step 1 of 6 · Pick 2 to 8',
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

  it('is the rule alone that the You tab cites under its own group title', () => {
    expect(socialTagsRule({ minimum: 2, maximum: 8 })).toBe('Pick 2 to 8');
  });
});

describe('the save control on the You tab', () => {
  it('shuts under the floor in the step’s own words, with the verb changed', () => {
    // ADR-0179 §2: *Continue* is *Save*, shut under the floor with the step's own words.
    expect(socialTagsSaveLabel({ kind: 'short', missing: 2 }, true)).toBe('Pick 2 tags to save');
    expect(socialTagsSaveLabel({ kind: 'short', missing: 1 }, true)).toBe(
      'Pick 1 more tag to save',
    );
  });

  it('says Save while the draft differs and Saved while it is the profile’s own', () => {
    expect(socialTagsSaveLabel({ kind: 'ready' }, true)).toBe('Save');
    expect(socialTagsSaveLabel({ kind: 'ready' }, false)).toBe('Saved');
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
    expect(socialTagCeilingTitle({ minimum: 2, maximum: 8 })).toBe('8 tags is the most');
    expect(socialTagCeilingTitle({ minimum: 2, maximum: 4 })).toBe('4 tags is the most');
  });
});
