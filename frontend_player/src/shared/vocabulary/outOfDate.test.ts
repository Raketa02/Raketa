/**
 * What a build says about a code it has never seen.
 *
 * The wording is the assertion here, because the sentence's whole job is to name *neither the
 * code nor the vocabulary*: a raw `SOCIAL_VIBE` is a wire token in a player's face, and *an
 * unknown evidence kind* is a sentence about our schema.
 */

import { OUT_OF_DATE_GAP, orOutOfDate } from './outOfDate';

describe('the gap', () => {
  it('tells the player what to do about it', () => {
    expect(OUT_OF_DATE_GAP).toBe('This app is too old to read this one — update Raketa.');
  });

  it('names neither the code nor the vocabulary it came from', () => {
    expect(OUT_OF_DATE_GAP).not.toMatch(/[A-Z]{2,}_|evidence|schema|kind|code/);
  });

  it('is one string, so five placements cannot drift into five sentences', () => {
    expect(orOutOfDate(undefined)).toBe(OUT_OF_DATE_GAP);
  });
});

describe('the helper', () => {
  it('leaves words this build has alone', () => {
    expect(orOutOfDate('Wants to play you')).toBe('Wants to play you');
  });
});
