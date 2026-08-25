/**
 * What the end of the part says when it cannot finish.
 *
 * The area is the case a player actually meets — the location step names the cost of
 * leaving without one and this is where it is collected. The radius is the case they
 * cannot: that step writes the served default into the draft the moment it knows it. Both
 * are covered here anyway, because a screen that only handles the case somebody predicted
 * is a screen with a blank state, and the way to keep the unpredicted one honest is to
 * drive it.
 */

import type { MissingAnswer } from '../domain/profileCommit';

import { answerStillWanted } from './commitPresentation';

describe('the answer the last step asks for', () => {
  it('is the area, when that is what the player continued past', () => {
    const wanted = answerStillWanted(['location', 'proposals-opt-in']);

    expect(wanted?.answer).toBe('location');
    expect(wanted?.copy.label).toBe('Set the area you play in');
  });

  it('is the earliest one, so two outstanding answers are not two round trips', () => {
    // `missing` is in step order. Sending the player to the later one would bounce them back
    // here only to be sent to the earlier one next.
    const wanted = answerStillWanted(['location', 'search-radius']);

    expect(wanted?.answer).toBe('location');
  });

  it('is the radius when that is the only one outstanding, rather than nothing at all', () => {
    const wanted = answerStillWanted(['search-radius']);

    expect(wanted?.answer).toBe('search-radius');
    expect(wanted?.copy.label).toBe('Set how far you will travel');
  });

  it('is nothing when the only question left is the one this step asks', () => {
    // There is no step to go back to: the two controls are immediately above the finish, and
    // what says so is the consent copy's own hint.
    expect(answerStillWanted(['proposals-opt-in'])).toBeUndefined();
  });

  it('is nothing when nothing is outstanding', () => {
    expect(answerStillWanted([])).toBeUndefined();
  });

  it('names a step to go back to for every answer that has one', () => {
    // The exhaustiveness the table is typed for, driven rather than asserted by the compiler
    // alone: a fourth answer added to `MissingAnswer` arrives here as a missing entry.
    const goesBack: readonly MissingAnswer[] = ['location', 'search-radius'];

    for (const answer of goesBack) {
      const wanted = answerStillWanted([answer]);
      expect(wanted?.answer).toBe(answer);
      expect(wanted?.copy.title.length).toBeGreaterThan(0);
      expect(wanted?.copy.finishHint.length).toBeGreaterThan(0);
    }
  });
});
