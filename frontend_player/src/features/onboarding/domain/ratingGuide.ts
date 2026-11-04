/**
 * **When _Your rating_ runs its guide** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §8): on a screen with a rating to explain, on a phone that has **never** shown it — whatever
 * the pass's origin, and whether the guide was finished or skipped the time it was shown.
 *
 * *Never* is the phone's answer, so a phone that has not answered yet is not *never*: the guide
 * waits for the read rather than opening and then vanishing under the player's thumb.
 *
 * @param hasRating the screen is drawing a rating — a run that ended without one has nothing to explain.
 * @param shownOnThisPhone the phone's flag, or `undefined` while it is being read.
 */
export function ratingGuideIsDue(
  hasRating: boolean,
  shownOnThisPhone: boolean | undefined,
): boolean {
  return hasRating && shownOnThisPhone === false;
}
