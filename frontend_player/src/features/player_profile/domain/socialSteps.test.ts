/**
 * The second part's step sequence, with no renderer and no router.
 *
 * Six screens in one order, and the two boundaries that are rules rather than layout: the
 * first step has nothing behind it, and the last has nothing in front of it but the commit.
 */

import { emptyDraft } from './ProfileDraft';
import { SOCIAL_STEPS, admissionToStep, stepAfter, stepBefore, stepPosition } from './socialSteps';

describe('the order of the second part', () => {
  it('asks the six questions in the order the spec sets', () => {
    expect(SOCIAL_STEPS).toEqual(['tags', 'intro', 'photos', 'availability', 'location', 'gender']);
  });

  it('asks who last of the matching questions, and never among the tags', () => {
    // Not incidental either. The tags step says what kind of player somebody is; the week,
    // the area and this one narrow who the platform will put in front of them, and a
    // preference over who you play with is one of those rather than another description of
    // yourself.
    expect(SOCIAL_STEPS.indexOf('gender')).toBeGreaterThan(SOCIAL_STEPS.indexOf('location'));
    expect(SOCIAL_STEPS.indexOf('gender')).toBeGreaterThan(SOCIAL_STEPS.indexOf('tags'));
  });

  it('ends on who you play with, which carries the finish', () => {
    // Nothing may come after the step that carries the finish, whatever else is added — and
    // since the radius and the proposals question left (#582) that step is *Who you play
    // with*, a question whose answer shapes every game a player is put in.
    expect(SOCIAL_STEPS[SOCIAL_STEPS.length - 1]).toBe('gender');
  });

  it('asks for the intro straight after the tags, and before the photos', () => {
    // *You've picked your tags; now say it in your own words* (ADR-0170 §5). The tags say
    // what kind of player somebody is in the platform's words, and the line is the same
    // question in their own — so it follows them, and it comes before the one step that
    // reaches the device.
    expect(SOCIAL_STEPS.indexOf('intro')).toBe(SOCIAL_STEPS.indexOf('tags') + 1);
    expect(SOCIAL_STEPS.indexOf('photos')).toBe(SOCIAL_STEPS.indexOf('intro') + 1);
  });
});

describe('moving forward', () => {
  it('leads from each step to the next', () => {
    expect(stepAfter('tags')).toBe('intro');
    expect(stepAfter('intro')).toBe('photos');
    expect(stepAfter('photos')).toBe('availability');
    expect(stepAfter('availability')).toBe('location');
    expect(stepAfter('location')).toBe('gender');
  });

  it('has nothing after the last step', () => {
    // What follows the last step is the commit, and a commit is not a step. Answering
    // "gender" with a seventh screen here is how a part would gain one by accident.
    expect(stepAfter('gender')).toBeUndefined();
  });
});

describe('moving back', () => {
  it('leads from each step to the one before it', () => {
    expect(stepBefore('intro')).toBe('tags');
    expect(stepBefore('photos')).toBe('intro');
    expect(stepBefore('availability')).toBe('photos');
    expect(stepBefore('location')).toBe('availability');
    expect(stepBefore('gender')).toBe('location');
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
    expect(stepPosition('intro')).toEqual({ index: 2, total: 6 });
    expect(stepPosition('gender')).toEqual({ index: 6, total: 6 });
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
