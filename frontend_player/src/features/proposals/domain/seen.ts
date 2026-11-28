/**
 * **What a group page's tabs count: the rows the player hasn't seen**
 * ([ADR-0208](../../../../../docs/adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md),
 * [#849](https://github.com/Rakieta02/Rakieta/issues/849); split Q2b, Q10). Beside the Fill in rules
 * (`fillIn.ts`), because Fill in and You’re in were the first tabs it counted; Games joined them
 * with the deck's ids (#850).
 *
 * Pure. A row is known by its id — a rescue by its booking, a yes or a card by its proposal — so **a
 * row that only changed** (a join, a new version, a deadline moved) **keeps its id and stays seen**,
 * and only an id the player has not had on screen counts. The phone keeps the result (the
 * phone-preferences store); it decides nothing.
 *
 * **A badge is a nudge, not a ledger** — the product owner's rule over every choice here: it never
 * costs a request or a wait, and where being exact would, the simpler rule wins.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import { GAME_KINDS, type GameKind } from './vocabulary';

/**
 * **The lists of seen rows a group page keeps** — Fill in's rescues, You’re in's live yeses, and
 * Games' cards with somebody In, **one list per kind** (ADR-0208 §1, #850): the group page's three
 * badged tabs, by its own names, spelled here because the page reads this feature and never the
 * reverse.
 *
 * **Games is per kind because the deck is read per kind.** A look cuts its list back to the ids the
 * read on screen counts, and the other kind's read — held from an earlier visit — can be older
 * than a card seen since: one list for both was cut back to it, and a card she had just looked at
 * was new again (the code review's catch). Each kind's list is cut back only by its own kind's
 * read, and the badge counts against both.
 */
export type SeenTab = 'fillIn' | 'youreIn' | GamesSeen;

/** **Games' list for one kind** — the cards of that kind seen on the deck. */
export type GamesSeen = `games.${GameKind}`;

export function gamesSeen(kind: GameKind): GamesSeen {
  return `games.${kind}`;
}

/** **What the Games badge is counted against** — both kinds' lists, since it counts both kinds. */
export const GAMES_SEEN: readonly GamesSeen[] = GAME_KINDS.map(gamesSeen);

/**
 * **A tab's badge** — the ids it counts now, minus the ids seen (ADR-0208 §1). 0 draws nothing, and
 * a seen id the tab no longer counts is simply not among them.
 */
export function unseenCount(counted: readonly string[], seen: readonly string[]): number {
  const looked = new Set(seen);
  return new Set(counted.filter((id) => !looked.has(id))).size;
}

/**
 * **What is seen after a look** — what was seen and what is on screen, **among the ids the tab
 * still counts** (ADR-0208 §2), so the set is cut back every time it is written and is never bigger
 * than the tab. In the tab's own order, each id once.
 */
export function afterALook(
  seen: readonly string[],
  onScreen: readonly string[],
  counted: readonly string[],
): readonly string[] {
  const looked = new Set([...seen, ...onScreen]);
  return [...new Set(counted)].filter((id) => looked.has(id));
}

/** Whether two seen sets hold the same ids — a look that changed nothing is never written. */
export function sameSeen(a: readonly string[], b: readonly string[]): boolean {
  const one = new Set(a);
  const other = new Set(b);
  return one.size === other.size && [...one].every((id) => other.has(id));
}

/**
 * **Where a list of seen ids is kept** — one entry per group, sport and tab, and on Games per kind
 * (ADR-0208 §1).
 */
export function seenEntry(groupId: string, sport: Sport, tab: SeenTab): string {
  return `${groupId}.${sport}.${tab}`;
}

/**
 * **What the phone kept for a tab** — the ids it saved, or **nothing seen** for a value it cannot
 * read or does not recognise (ADR-0208 §4): never an error, and the worst it does is show a badge
 * the player had already cleared. Only a list of ids is a value; anything else is stale whole.
 */
export function seenFrom(saved: string | undefined): readonly string[] {
  if (saved === undefined) return [];
  try {
    const parsed: unknown = JSON.parse(saved);
    return Array.isArray(parsed) && parsed.every((id) => typeof id === 'string') ? parsed : [];
  } catch {
    return [];
  }
}
