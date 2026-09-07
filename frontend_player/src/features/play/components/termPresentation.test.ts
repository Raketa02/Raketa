/**
 * The eight row heads.
 *
 * Copy changes; two things must not. **Every term has words** — which the type already forces
 * and this restates in a form that fails loudly — and **no two terms read alike**, since two
 * rows sharing a head are two contributions a player cannot tell apart.
 */

import { TERMS } from '../domain/vocabulary';

import { termLabel } from './termPresentation';

describe('what a term is called', () => {
  it('gives all eight their own words', () => {
    const labels = TERMS.map(termLabel);

    expect(labels.every((label) => label.length > 0)).toBe(true);
    expect(new Set(labels).size).toBe(TERMS.length);
  });

  it('names the two tag terms by where they are read, not by their tag group', () => {
    // The split is by *relationship*: the same tag can be read for the hour on court in one
    // matrix row and for the evening around it in another.
    expect(termLabel('PLAYING_STYLE')).toBe('On court');
    expect(termLabel('SOCIAL_VIBE')).toBe('Around the game');
  });

  it('grades nothing in a head', () => {
    // A head is a noun: the row prints the figure, and a head that graded it would be the
    // client's judgement standing over the engine's number.
    for (const label of TERMS.map(termLabel)) {
      expect(label).not.toMatch(/\b(good|strong|poor|bad|well)\b/i);
    }
  });
});
