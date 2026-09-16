/**
 * When the phone is read again **without anybody pressing anything** — the cold-start
 * refresh's one rule ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6).
 *
 * A location is written once, at the end of onboarding, and the radar draws a city as it
 * was. So the app re-reads the phone **on every cold start** and **on a return from the
 * background after more than a day** — and never merely on foreground, which the author
 * refused as tracking: a player who flips to Messages and back has not gone anywhere, and
 * a read on every return is a movement trail taken a foreground at a time.
 *
 * The cold start needs no rule — a new process has read nothing — so what is here is the
 * floor under the foreground. The instant it is measured against is the last time a
 * refresh was *attempted*, whatever came of it: a refused permission or an empty fix is
 * still the phone having been asked, and asking again on the next foreground would be the
 * tracking the day was chosen against.
 */

/** A day. Exactly a day is still inside the floor; a moment more is not. */
export const FOREGROUND_REFRESH_FLOOR_MS = 24 * 60 * 60 * 1000;

/**
 * Whether a return from the background is old enough to read the phone again.
 *
 * Both instants are the device's own clock in milliseconds — a per-device convenience that
 * nothing else reads, so there is no `read_at` to measure from and no reason to want one.
 */
export function foregroundRefreshDue(lastRefreshAt: number, now: number): boolean {
  return now - lastRefreshAt > FOREGROUND_REFRESH_FLOOR_MS;
}
