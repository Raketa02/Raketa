/**
 * **A people row's See all** ([#801](https://github.com/Rakieta02/Rakieta/issues/801),
 * [#802](https://github.com/Rakieta02/Rakieta/issues/802); the Home rows mechanics §6.7, §7.4) — a
 * plain list in the server's order, 20 to a page, and a sport pill: *All*, then the sports the server
 * offers. New in Rakieta and Same competitive level read it the same way; who is on it, in which order,
 * and which sports the pill offers are the server's.
 */

import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

/**
 * **What See all is filtered by** — *All*, or one sport. `'all'` is the sport pill's own *All*
 * (`shared/ui`'s `ALL_SPORTS`), spelled here since the domain draws nothing.
 */
export type SeeAllSport = Sport | 'all';

/** The sport See all asks the server for — none for *All*. */
export function pageSport(choice: SeeAllSport): Sport | undefined {
  return choice === 'all' ? undefined : choice;
}

/** **Which page of See all to read** — a sport, or every one, and the cursor it is read after. */
export interface SeeAllAsk {
  readonly sport: Sport | undefined;
  readonly after: string | undefined;
}

/** **One page of See all** — up to 20 people, the cursor behind them, and the pill's sports. */
export interface SeeAllPage<Person> {
  readonly people: readonly Person[];
  /** Read the next page `after` this — absent on the last. */
  readonly next?: string;
  /** The sports the pill offers beside *All*, in the sports' own order. */
  readonly sports: readonly Sport[];
}

/**
 * **See all's list** — the pages in the order read, **each person once**: a page read after the
 * crowd moved can hold a person the page before it already drew, and a list keyed by player cannot
 * draw them twice.
 */
export function joinPages<Person extends { readonly playerId: string }>(
  pages: readonly SeeAllPage<Person>[],
): readonly Person[] {
  const seen = new Set<string>();
  return pages.flatMap((page) =>
    page.people.filter((person) => {
      if (seen.has(person.playerId)) return false;
      seen.add(person.playerId);
      return true;
    }),
  );
}

/**
 * **The pill's choices** — *All*, then the sports the server offers. **The chosen sport stays**
 * though it left that list since it was offered (*Nobody new plays squash yet*), so the pill never
 * drops the sport it stands on.
 */
export function pillChoices(served: readonly Sport[], chosen: SeeAllSport): readonly SeeAllSport[] {
  const sports = SPORTS.filter((sport) => served.includes(sport) || sport === chosen);
  return ['all', ...sports];
}
