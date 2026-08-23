/**
 * How long a sport-bar selection lasts: one visit, and a visit ends after thirty
 * minutes away.
 *
 * `ADR-0084` decides the default outright, on a specific harm rather than on
 * taste: the filter hides **the enrolled strip** as well as the shelves, so a
 * remembered filter can hide a match the player has paid for and is playing
 * tomorrow. That is a different class of mistake from showing her too much.
 *
 * **A cold start is not the boundary.** Phones do not close apps, so *reset on
 * launch* would almost never fire and the protection would be decorative.
 * Stepping out to answer a text keeps the filter; coming back the next morning
 * does not.
 *
 * The half-hour is the conventional session boundary and `ADR-0084` records that
 * nothing measures whether it is right. It lives here, as a rule with a name, so
 * that changing it is one edit against one test rather than a number found in a
 * hook.
 */

/** Thirty minutes away ends a visit. */
export const VISIT_GAP_MS = 30 * 60 * 1000;

/**
 * Whether a selection made at `lastSeenAt` is still the same visit at `now`.
 *
 * A selection with no `lastSeenAt` has never been made, so there is nothing to
 * survive and the answer is `false` — which resolves to `all`, the default.
 * Exactly thirty minutes still counts: the boundary is *more than* half an hour
 * away, so the common case of a round number does not fall on the strict side.
 */
export function withinSameVisit(lastSeenAt: number | undefined, now: number): boolean {
  if (lastSeenAt === undefined) return false;
  return now - lastSeenAt <= VISIT_GAP_MS;
}
