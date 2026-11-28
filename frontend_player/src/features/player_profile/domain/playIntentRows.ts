/**
 * **Which sports the profile lists a declaration for, and which of them have none.**
 *
 * Two rules, and both are the sort a screen would otherwise answer inline
 * ([#296](https://github.com/Rakieta02/Rakieta/issues/296)):
 *
 * **An unrated sport is not a row.** A rating is what makes a sport matchable — every
 * matchmaking route is keyed by one — so offering the question for a sport nobody has been
 * rated in would collect an answer no search could ever read. The list is therefore a
 * projection of `GET /ratings`, exactly as Play's sport chips are, and never of the four the
 * platform happens to know about.
 *
 * **Absence is *undeclared*, and it is a fact worth drawing.** ADR-0094 forbids a null intent
 * on the wire, so the map holds only what was answered; the row for a sport that is not in it
 * is the first place in the app a player can discover that a search there would be refused
 * *before* trying to run one. Which is why the pair is a row with an absent value rather than
 * a row that is missing.
 */

import type { PlayIntent } from '@/shared/vocabulary/playIntent';
import type { Sport } from '@/shared/vocabulary/sport';

import type { PlayIntentDeclarations } from './PlayerProfileSurface';

/** One sport the player is rated in, and what — if anything — they have declared in it. */
export interface PlayIntentRow {
  readonly sport: Sport;
  /** `undefined` is *never asked*, and never `NO_PREFERENCE`. */
  readonly intent: PlayIntent | undefined;
}

/**
 * The rows, in the order the ratings arrived.
 *
 * **Nothing sorts.** `GET /ratings` answers in sport-registry order and so does Play's chip
 * row, so a player meets their sports in one order everywhere — the same argument
 * `sportOnScreen` makes for taking *the first rated sport* off the served list.
 */
export function playIntentRows(
  rated: readonly Sport[],
  declarations: PlayIntentDeclarations,
): readonly PlayIntentRow[] {
  return rated.map((sport) => ({ sport, intent: declarations[sport] }));
}

/**
 * Whether anything on the list is still unanswered — the one condition the sentence about
 * *Not set* is drawn under.
 *
 * A sentence describing a state nobody is in is chrome, which is the whole reason this is a
 * question rather than a line that is always there.
 */
export function anySportUndeclared(rows: readonly PlayIntentRow[]): boolean {
  return rows.some((row) => row.intent === undefined);
}
