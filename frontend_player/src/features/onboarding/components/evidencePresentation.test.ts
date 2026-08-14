/**
 * The two resolutions the evidence trail makes, and the fallback that is the point of
 * both: a key or a direction this build has never seen must still reach the screen.
 */

import { directionMark, widenerVariant } from './evidencePresentation';

describe('what widened the range', () => {
  it('emphasises the two keys it recognises, and neither is a failure colour', () => {
    // A contradiction is `watch this, reversible, not yet wrong` — never coral and never
    // red. The app did not pick a side and is not accusing anybody of anything.
    expect(widenerVariant('answers-disagreed')).toBe('amber');
    expect(widenerVariant('time-away')).toBe('info');
  });

  it('renders a key it has never seen with the default treatment', () => {
    // The correctness requirement, not a nicety: old versions live on real phones for
    // months, and a widener missing from the trail leaves a player reading a range that
    // nothing on the screen accounts for.
    expect(widenerVariant('lunar-cycle')).toBe('base');
    expect(widenerVariant('')).toBe('base');
  });
});

describe('which way a category pulled', () => {
  it('carries a shape and a word for each direction the engine computes', () => {
    // Never colour alone — Part 13. Both halves are here because a shape on its own is
    // not readable either, and the spoken form is what a screen reader gets.
    expect(directionMark('up')).toEqual({ glyph: '▲', word: 'Above', spoken: 'above your level' });
    expect(directionMark('down')?.word).toBe('Below');
    expect(directionMark('neutral')?.word).toBe('In line');
  });

  it('draws no mark for a direction it cannot read, rather than guessing one', () => {
    // A client-side arrow is a second opinion about the arithmetic. Where this build
    // cannot read the engine's word, the row still shows the category and its level —
    // the part the client did not invent — and claims no direction at all.
    expect(directionMark('sideways')).toBeUndefined();
    expect(directionMark('UP')).toBeUndefined();
  });
});
