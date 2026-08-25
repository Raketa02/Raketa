/**
 * The second part's step sequence, with no renderer and no router.
 *
 * Six screens in one order, and the two boundaries that are rules rather than layout: the
 * first step has nothing behind it, and the last has nothing in front of it until the
 * commit exists.
 */

import { emptyDraft } from './ProfileDraft';
import { SOCIAL_STEPS, admissionToStep, stepAfter, stepBefore, stepPosition } from './socialSteps';

describe('the order of the second part', () => {
  it('asks the six questions in the order the spec sets', () => {
    expect(SOCIAL_STEPS).toEqual([
      'tags',
      'photos',
      'availability',
      'location',
      'radius',
      'opt-in',
    ]);
  });

  it('asks where before how far', () => {
    // Not incidental ordering. "How far out do you want to look" is meaningless until the
    // player has said where they are looking from, so location precedes radius.
    expect(SOCIAL_STEPS.indexOf('location')).toBeLessThan(SOCIAL_STEPS.indexOf('radius'));
  });
});

describe('moving forward', () => {
  it('leads from each step to the next', () => {
    expect(stepAfter('tags')).toBe('photos');
    expect(stepAfter('photos')).toBe('availability');
    expect(stepAfter('availability')).toBe('location');
    expect(stepAfter('location')).toBe('radius');
    expect(stepAfter('radius')).toBe('opt-in');
  });

  it('has nothing after the last step', () => {
    // What follows the last step is the commit, and a commit is not a step. Answering
    // "opt-in" with a seventh screen here is how a part would gain one by accident.
    expect(stepAfter('opt-in')).toBeUndefined();
  });
});

describe('moving back', () => {
  it('leads from each step to the one before it', () => {
    expect(stepBefore('photos')).toBe('tags');
    expect(stepBefore('availability')).toBe('photos');
    expect(stepBefore('location')).toBe('availability');
    expect(stepBefore('radius')).toBe('location');
    expect(stepBefore('opt-in')).toBe('radius');
  });

  it('has nothing before the first step', () => {
    // The part boundary, and it is hard in both directions. Behind step one is a rated
    // Assessment's review, and an answer is revisable for as long as its run is and no
    // longer — the same clamp the questionnaire's first question already carries.
    expect(stepBefore('tags')).toBeUndefined();
  });
});

describe('where a step sits', () => {
  it('counts from one, out of six', () => {
    expect(stepPosition('tags')).toEqual({ index: 1, total: 6 });
    expect(stepPosition('opt-in')).toEqual({ index: 6, total: 6 });
  });
});

describe('who may be dropped onto a step', () => {
  it('starts the part at the first step when none is running', () => {
    // The door. The entry gate redirects here, and there is nothing to admit them to yet.
    expect(admissionToStep('tags', undefined)).toEqual({ kind: 'enter' });
  });

  it('sends a step in the middle back to the beginning when no part is running', () => {
    // A hand-built link, a stale notification, an old deep link. Continuing from here would
    // commit a profile built from screens the player never saw.
    for (const step of SOCIAL_STEPS.slice(1)) {
      expect(admissionToStep(step, undefined)).toEqual({ kind: 'start-over' });
    }
  });

  it('admits every step, including the first, once the part is running', () => {
    // Walking *back* to step one is an ordinary move, and it must not read as a fresh
    // entry — beginning again there would wipe the answers the player walked back past.
    for (const step of SOCIAL_STEPS) {
      expect(admissionToStep(step, emptyDraft())).toEqual({ kind: 'admit' });
    }
  });
});
