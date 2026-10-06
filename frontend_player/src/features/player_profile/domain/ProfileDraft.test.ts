/**
 * The draft, with no store and no renderer.
 *
 * What is being pinned here is that recording one answer leaves the others alone — which
 * is the whole promise the part makes when it says back and forward are free.
 */

import { emptyDraft, recordAnswer } from './ProfileDraft';

describe('a draft that has been started', () => {
  it('holds nothing, and says so without using an empty value to mean it', () => {
    const draft = emptyDraft();

    // A blank week and no photos are legitimate *answers* — an empty grid means no
    // preference and never "leave me out" — so those two start as empty lists rather than
    // as absences, and the intro starts as nothing written for the same reason: a player
    // who skips has no line, not a missing one. The two that must actually be answered
    // start absent.
    //
    // `genderPreference` is neither: it starts at a **value**, because unconstrained is
    // what having narrowed nothing already means. It is the one field here that a step
    // cannot have failed to collect, and reading its default as an absence would invent a
    // third outstanding answer nobody is short of.
    expect(draft).toEqual({
      socialTagIds: [],
      intro: '',
      photoIds: [],
      weeklyHours: [],
      location: undefined,
      gender: undefined,
      genderPreference: 'any',
    });
  });
});

describe('recording an answer', () => {
  it('keeps every other answer', () => {
    // The reason the draft exists at all: walking back to check one thing must not cost
    // the player the rest.
    const walked = recordAnswer(
      recordAnswer(recordAnswer(emptyDraft(), { gender: 'man' }), {
        weeklyHours: [{ day: 1, hour: 9 }],
      }),
      { location: { latitude: 41.39, longitude: 2.16 } },
    );

    expect(walked.gender).toBe('man');
    expect(walked.weeklyHours).toEqual([{ day: 1, hour: 9 }]);
    expect(walked.location).toEqual({ latitude: 41.39, longitude: 2.16 });
  });

  it('replaces the answer to the step that was answered again', () => {
    const changed = recordAnswer(recordAnswer(emptyDraft(), { gender: 'man' }), {
      gender: 'prefer-not-to-say',
    });

    expect(changed.gender).toBe('prefer-not-to-say');
  });

  it('leaves the draft it was given untouched', () => {
    // Nothing mutates: the store swaps one value for another, and a Zustand selector that
    // was handed a mutated object would not re-render the screen reading it.
    const before = emptyDraft();
    recordAnswer(before, { gender: 'woman' });

    expect(before.gender).toBeUndefined();
  });
});
