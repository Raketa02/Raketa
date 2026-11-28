/**
 * **The reveal's rule for a screen with several parts** (design system 5.6; PRD #867,
 * [#871](https://github.com/Rakieta02/Rakieta/issues/871); the loading shimmer log §5, Q11, Q13) —
 * which of a screen's parts, named top-down, are shown, from what its reads have done and how long it
 * has been up. Pure; `useRevealParts` wraps it with the ceiling's one timer.
 *
 * - **Before the ceiling, everything is revealed together**, once every part has finished: one
 *   reveal, the finished screen shown once rather than watched as it assembles.
 * - **At the ceiling, the finished parts are revealed from the top, stopping at the first that has
 *   not finished.** That part and everything below it keep their skeleton, and after that each part
 *   is revealed in order as it finishes. **A lower part never appears before an upper one**, so
 *   nothing is ever pushed down under the reader — the harm the research names (web.dev's layout
 *   shift; React's `revealOrder="forwards"`).
 * - **A part shown stays shown** for the rest of the mount, whatever its reads do next: a pull, a
 *   background re-read.
 *
 * Whether a part has finished is the screen's — its reads landed, refused, paused for a connection,
 * or failed once and retrying (`shared/lib/query-client`'s `readHasFinished`). Since a part is shown
 * only after every part above it, what is shown is always the top of the list, so it is a count.
 */

/**
 * **The ceiling**, 2.5 s from the screen's mount: the moment React 19.2 stops holding Suspense
 * boundaries back to reveal them together, borrowed from Google's "good" Largest Contentful Paint
 * (the loading shimmer log §2.7, Q11, Q13). Past it, a screen stops waiting for its slowest part.
 */
export const REVEAL_CEILING = 2_500;

export interface PartsShown {
  /** Each part's finished flag, top-down. */
  readonly finished: readonly boolean[];
  /** Whether the ceiling has passed since the screen mounted. */
  readonly pastCeiling: boolean;
  /** How many parts, from the top, are already shown. */
  readonly shown: number;
}

/** **How many parts, from the top, to show** — never fewer than are shown already. */
export function partsToShow({ finished, pastCeiling, shown }: PartsShown): number {
  if (finished.every(Boolean)) return finished.length;
  if (!pastCeiling) return shown;
  const ready = finished.indexOf(false);
  return Math.max(shown, ready);
}
