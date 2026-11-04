/**
 * **When _Your rating_ runs its guide** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §8) — with no renderer: a rating to explain, on a phone that has never shown the guide.
 */

import { ratingGuideIsDue } from './ratingGuide';

describe('the guide on Your rating', () => {
  it('runs on a rating, on a phone that has never shown it', () => {
    expect(ratingGuideIsDue(true, false)).toBe(true);
  });

  it('never runs again on a phone that has shown it', () => {
    expect(ratingGuideIsDue(true, true)).toBe(false);
  });

  it('waits for the phone to answer, rather than running on a guess', () => {
    expect(ratingGuideIsDue(true, undefined)).toBe(false);
  });

  it('has nothing to explain until the rating is on the screen', () => {
    expect(ratingGuideIsDue(false, false)).toBe(false);
  });
});
