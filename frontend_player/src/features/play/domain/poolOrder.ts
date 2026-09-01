/**
 * **Re-sorting the pool** — which chips the row draws, and what each of them does to rows the
 * screen already holds.
 *
 * *"Re-sorting costs no round trip"*: `sorts_available` is a list of orderings over fields
 * every row already carries, so **a sort is in no query key at all** — a key per sort would
 * mint a cache entry per chip and a request behind each one (`hooks/searchKeys.ts`).
 *
 * ## The vocabulary is the server's, and the row vanishes when it is empty
 *
 * §C5 specified a fixed row of four chips. Today the server offers **at most two**: `EVENEST`
 * never, `MOST_RELIABLE` not until the Player Score ships, and `sorts_available == []` is a
 * real state with a test asserting it. So the row is rendered from the list and omitted
 * entirely when it is empty ([#231](https://github.com/Raketa02/Raketa/issues/231) §6) — a
 * hardcoded four would be three-quarters a lie.
 *
 * ## The returned order becomes selectable once the player has left it
 *
 * This is the non-obvious half. `BEST_FIT` is *withheld precisely when the returned order
 * already is best-fit order* — the engine breaks ties on `(rank_key desc, fit desc, player_id
 * asc)` and Liveness reorders `rank_key` without entering Fit, so the chip is offered exactly
 * when sorting by the printed number genuinely moves rows. If the only chip offered is
 * *Closest*, tapping it strands the player with no control representing where they came from,
 * and **a sort control that cannot restore the default is a one-way door**.
 *
 * So the way back is added to the row — and it is `BEST_FIT` itself rather than a fourth
 * concept, which is exact rather than convenient: in the state where it is added, fit order
 * and the returned order are the same order, which is the very reason the server withheld it.
 *
 * ## A chip this build cannot order by is not drawn
 *
 * `EVENEST` reads `would_be_forecast` — **out of scope entirely**, since nothing in the
 * backend writes it and its three consumers went with it (#231 §4) — and `MOST_RELIABLE`
 * reads a published Player Score that does not cross the wire. Neither is offered today.
 * Both keep a word so the table is exhaustive by type, and the comparator table is exhaustive
 * the same way: a sort added to the vocabulary and not to this table does not compile, and one
 * that has no ordering here says so as `undefined` rather than as a chip that does nothing.
 *
 * That is **not** deriving offerability from the rows, which is the move that promoted
 * `sorts_available` to the server in the first place. It is this build declaring which
 * orderings it can perform over the fields a `Candidate` actually carries — the same §3 drop a
 * social tag with no words takes.
 */

import type { Candidate } from './candidate';
import { SORT_OPTIONS, type SortOption } from './vocabulary';

type Comparator = (one: Candidate, other: Candidate) => number;

/**
 * How each sort orders rows already held — and `undefined` where this build cannot.
 *
 * Exhaustive by type over `SortOption`, which is what makes the day a sort becomes offerable
 * a change to this one table.
 */
const COMPARATOR: Readonly<Record<SortOption, Comparator | undefined>> = {
  /** The printed number, descending. Ties keep the order the engine served them in. */
  BEST_FIT: (one, other) => other.fit - one.fit,
  /**
   * Kilometres, ascending, with **a stood-down distance last rather than first**.
   *
   * The omission is the term standing down and not a zero — the two spellings of absence, and
   * the reason `distance_km` was promoted out of the distance evidence at all.
   */
  CLOSEST: (one, other) => farthest(one) - farthest(other),
  EVENEST: undefined,
  MOST_RELIABLE: undefined,
};

const farthest = (row: Candidate) => row.distanceKm ?? Number.POSITIVE_INFINITY;

const ORDERABLE: readonly SortOption[] = SORT_OPTIONS.filter(
  (sort) => COMPARATOR[sort] !== undefined,
);

/**
 * The rows, in the order the screen should draw them.
 *
 * `undefined` is *the order they arrived in*, which is the engine's own ranking and the pool's
 * default. `Array.prototype.sort` is stable, so a sort leaves rows it cannot separate exactly
 * where the answer put them.
 */
export function orderPool(
  rows: readonly Candidate[],
  sort: SortOption | undefined,
): readonly Candidate[] {
  const compare = sort === undefined ? undefined : COMPARATOR[sort];
  return compare === undefined ? rows : [...rows].sort(compare);
}

/**
 * The chips to draw, in the order the server offered them — plus the way back, once there is
 * somewhere to come back from.
 *
 * @param available `SearchEnvelope.sortsAvailable`, verbatim.
 * @param chosen what the player has selected, or `undefined` for the order they arrived in.
 */
export function poolSortRow(
  available: readonly SortOption[],
  chosen: SortOption | undefined,
): readonly SortOption[] {
  const offered = available.filter((sort) => ORDERABLE.includes(sort));
  const stranded = chosen !== undefined && !offered.includes('BEST_FIT');
  return stranded ? ['BEST_FIT', ...offered] : offered;
}
