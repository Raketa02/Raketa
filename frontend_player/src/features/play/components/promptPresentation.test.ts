/**
 * The four questions a search raises.
 *
 * Three things are asserted rather than the wording. Every prompt quotes **the value already
 * in play** and never one this build chose; every one closes with §F2's closer, so none of
 * them can read as a gate; and the suppression sentence is a **typed absence** on the one
 * prompt that has none, rather than a string somebody forgot.
 */

import { PROMPTS } from '../domain/vocabulary';

import {
  PROMPT_CLOSER,
  REFRESH_YOUR_TIMES_BODY,
  promptCopy,
  promptSuppression,
} from './promptPresentation';

describe('every prompt quotes the value already in play', () => {
  it('names the radius the player keeps taking', () => {
    expect(promptCopy({ prompt: 'KEEP_THIS_RADIUS', radiusKm: 15 }).title).toBe('Keep 15 km?');
    expect(promptCopy({ prompt: 'KEEP_THIS_RADIUS', radiusKm: 30 }).title).toBe('Keep 30 km?');
  });

  it('names both weeks: the one just used and the one on file', () => {
    expect(promptCopy({ prompt: 'KEEP_THESE_TIMES', slotsNow: 6, slotsWas: 4 }).body).toMatch(
      /^6 slots now · 4 on your profile\./,
    );
  });

  it('hardcodes no plural, in a body the deck wrote with one', () => {
    // §19: no string here hardcodes an `s`, and a week of one cell is a legal week to be
    // offered — an empty one is too.
    expect(promptCopy({ prompt: 'KEEP_THESE_TIMES', slotsNow: 1, slotsWas: 4 }).body).toMatch(
      /^1 slot now/,
    );
  });

  it('names the marks the grid draws, and never the colour it draws them in', () => {
    // 6.8's diff variant replaced the volt ring and the 45% opacity with a plus and a dash,
    // so the sentence that named the retired scheme described marks nobody could see.
    const body = promptCopy({ prompt: 'KEEP_THESE_TIMES', slotsNow: 6, slotsWas: 4 }).body;

    expect(body).toBe('6 slots now · 4 on your profile. A plus is new, a dash is one you dropped.');
    expect(body).not.toMatch(/green|ring|faded/i);
  });

  it('tells a cleared week what happens to it, rather than counting it as nought', () => {
    // ADR-0102: a blank grid is *absent*, never *never*. `0 slots now` asserts the one
    // measurement the matcher refuses to take, on the week where the whole grid is the
    // dropped half and there is no new one to describe.
    const body = promptCopy({ prompt: 'KEEP_THESE_TIMES', slotsNow: 0, slotsWas: 4 }).body;

    expect(body).toBe(
      'Nothing ticked · 4 on your profile. The matcher skips a blank week rather than scoring ' +
        'it nought.',
    );
    expect(body).not.toMatch(/0 slots/);
  });

  it('closes a cleared week the same way, and still offers it no suppression', () => {
    const copy = promptCopy({ prompt: 'KEEP_THESE_TIMES', slotsNow: 0, slotsWas: 4 });

    expect(copy.title).toBe('Keep these times?');
    expect(copy.closer).toBe(PROMPT_CLOSER);
    expect(copy.suppression).toBeUndefined();
  });

  it('names the sport and the mode the searches keep choosing', () => {
    expect(
      promptCopy({ prompt: 'UPDATE_PLAY_INTENT', sportName: 'Padel', mode: 'FOR_FUN' }).body,
    ).toBe(
      'Your last five Padel searches were for fun. Your profile still says otherwise — want to change it?',
    );
    expect(
      promptCopy({ prompt: 'UPDATE_PLAY_INTENT', sportName: 'Squash', mode: 'COMPETITIVE' }).body,
    ).toMatch(/five Squash searches were competitive/);
  });

  it('gives every prompt a title and a body, through one exhaustive call', () => {
    // §1's mechanism: a fifth prompt with no arm does not compile, which is what the flat
    // `Record` would have bought if two of these quoted no value.
    const raised = [
      { prompt: 'KEEP_THESE_TIMES', slotsNow: 6, slotsWas: 4 },
      { prompt: 'KEEP_THIS_RADIUS', radiusKm: 15 },
      { prompt: 'UPDATE_PLAY_INTENT', sportName: 'Padel', mode: 'FOR_FUN' },
      { prompt: 'REFRESH_YOUR_TIMES' },
    ] as const;

    for (const one of raised) {
      const copy = promptCopy(one);

      expect(copy.title.length).toBeGreaterThan(0);
      expect(copy.body.length).toBeGreaterThan(0);
      expect(copy.closer).toBe(PROMPT_CLOSER);
    }
  });
});

describe('the closer, and what declining costs', () => {
  it('never blocks', () => {
    expect(PROMPT_CLOSER).toBe('Either way the search runs now.');
  });

  it('carries the closer on every prompt it draws', () => {
    expect(promptCopy({ prompt: 'REFRESH_YOUR_TIMES' }).closer).toBe(PROMPT_CLOSER);
  });

  it('says a decline is remembered, on the three where it is', () => {
    // A decline writes no value, so it is the one answer nothing else would record — and a
    // thirty-day silence nobody is told about is a hidden mechanism.
    for (const prompt of [
      'KEEP_THIS_RADIUS',
      'UPDATE_PLAY_INTENT',
      'REFRESH_YOUR_TIMES',
    ] as const) {
      expect(promptSuppression(prompt)).toBe('Not now means not for a month.');
    }
  });

  it('offers no suppression at all on the times prompt', () => {
    // A grid legitimately differs per search where a radius, a declaration and a described
    // week do not, so this one is asked again.
    expect(promptSuppression('KEEP_THESE_TIMES')).toBeUndefined();
    expect(
      promptCopy({ prompt: 'KEEP_THESE_TIMES', slotsNow: 6, slotsWas: 4 }).suppression,
    ).toBeUndefined();
  });

  it('decides the question for every prompt in the vocabulary', () => {
    // The table is a full Record: a fifth prompt would have to answer this rather than
    // inherit a blank.
    for (const prompt of PROMPTS) {
      const suppression = promptSuppression(prompt);
      expect(suppression === undefined || suppression.length > 0).toBe(true);
    }
  });
});

describe('the one string kept verbatim', () => {
  it('is §F2 #9, in the prompt it was written for', () => {
    // One of the ten strings that define the voice: a copy edit here is an edit to the voice.
    expect(REFRESH_YOUR_TIMES_BODY).toMatch(/^The matcher reads this grid every time/);
    expect(REFRESH_YOUR_TIMES_BODY).toMatch(/quietly ruins every match it touches/);
  });

  it('leaves the radius body naming the habit rather than the number', () => {
    const body = promptCopy({ prompt: 'KEEP_THIS_RADIUS', radiusKm: 15 }).body;

    expect(body).toMatch(/three searches running/);
    expect(body).not.toMatch(/\d+ km/);
  });

  it('asks the times question as a question', () => {
    expect(promptCopy({ prompt: 'KEEP_THESE_TIMES', slotsNow: 6, slotsWas: 4 }).title).toBe(
      'Keep these times?',
    );
  });
});
