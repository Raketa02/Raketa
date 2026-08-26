/**
 * The one resolution the evidence trail makes, and the fallback that is the point of it: a
 * direction this build has never seen must not become an invented arrow.
 */

import { directionMark } from './evidencePresentation';

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
