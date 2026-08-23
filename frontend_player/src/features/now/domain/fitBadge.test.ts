/**
 * The badge's display bound — `ADR-0037`'s clamp, and the only arithmetic this
 * feature does to a score.
 *
 * The interesting cases are the two ends, because both are **reachable**: the
 * shipped engine was measured at 8 to 100 over 60 000 draws, so the pill would
 * otherwise print numbers the decision refuses in both directions — a 3 that is not
 * more useful than a 20, and a 100 that claims a certainty nothing warrants.
 */

import { BADGE_MAX, BADGE_MIN, MAX_REASONS, clampBadgeScore } from './fitBadge';

describe('the badge always prints a number, clamped 20–99', () => {
  it('prints a score inside the band exactly as it arrived', () => {
    expect(clampBadgeScore(74)).toBe(74);
    expect(clampBadgeScore(BADGE_MIN)).toBe(BADGE_MIN);
    expect(clampBadgeScore(BADGE_MAX)).toBe(BADGE_MAX);
  });

  it('raises everything below the floor to it', () => {
    // Both mean *no*, and a 3 is not more informative than a 20.
    expect(clampBadgeScore(8)).toBe(BADGE_MIN);
    expect(clampBadgeScore(19)).toBe(BADGE_MIN);
    expect(clampBadgeScore(0)).toBe(BADGE_MIN);
  });

  it('never reaches 100, because certainty is never warranted', () => {
    expect(clampBadgeScore(100)).toBe(BADGE_MAX);
    expect(clampBadgeScore(99.6)).toBe(BADGE_MAX);
  });

  it('prints an integer, so no badge ever shows a decimal', () => {
    expect(clampBadgeScore(74.4)).toBe(74);
    expect(clampBadgeScore(74.5)).toBe(75);
  });

  it('holds the two bounds the decision names, and three reasons', () => {
    // Pinned to their literals: a bound compared against itself is a test that
    // cannot fail, and these three are the whole of what the display owes.
    expect(BADGE_MIN).toBe(20);
    expect(BADGE_MAX).toBe(99);
    expect(MAX_REASONS).toBe(3);
  });
});
