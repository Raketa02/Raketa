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
 * §C5 specified a fixed row of four chips. Today the server offers **at most three**:
 * `EVENEST` never, `MOST_RELIABLE` only on a search whose candidates have a record — most
 * people have none, so most searches still do not carry it — and `sorts_available == []` is a
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
 * backend writes it and its three consumers went with it (#231 §4) — so it keeps a word and no
 * ordering. `MOST_RELIABLE` had the same shape until the published Player Score reached the
 * card ([#306](https://github.com/Raketa02/Raketa/issues/306)), and it is now an ordering like
 * any other. The comparator table stays exhaustive by type: a sort added to the vocabulary and
 * not to this table does not compile, and one this build cannot perform says so as `undefined`
 * rather than as a chip that does nothing.
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
  /**
   * The published Player Score, descending, with **an absent score last rather than first**.
   *
   * `CLOSEST`'s rule for `CLOSEST`'s reason: the omission is *the platform has watched this
   * person do nothing*, and a `0` read out of it would sort them as the least reliable people
   * on the list rather than as the ones there is nothing to say about.
   */
  MOST_RELIABLE: (one, other) => reliability(other) - reliability(one),
};

const farthest = (row: Candidate) => row.distanceKm ?? Number.POSITIVE_INFINITY;

/**
 * The score, with **no record as the lowest reading there is** — so subtracting the other way
 * round, which is what descending order is, puts them last.
 *
 * The sentinel goes the opposite way from `farthest`'s and the sense of the comparator does
 * too, because *closest* is ascending and *most reliable* is descending. Both say the same
 * thing about the same absence: it sorts last, never first.
 */
const reliability = (row: Candidate) => row.card.playerScore ?? Number.NEGATIVE_INFINITY;

const ORDERABLE: readonly SortOption[] = SORT_OPTIONS.filter(
  (sort) => COMPARATOR[sort] !== undefined,
);

/**
 * The rows the pool may **offer**, which is the answer's rows minus anybody already on court.
 *
 * A row for somebody who is already seated carries an *Add* that could do nothing, and that is
 * the same objection that keeps a sort nobody can act on off this screen: a visible control
 * that does nothing is the product lying quietly.
 *
 * **The ladder does not read this.** How many people cleared the bar is a fact about the
 * answer, and it must not move because the player has since seated one of them — the two
 * numbers are on screen together, and a title that counted what is left would be describing
 * the list rather than the search.
 */
export function pickable(
  rows: readonly Candidate[],
  seated: readonly string[],
): readonly Candidate[] {
  const onCourt = new Set(seated);
  return rows.filter((row) => !onCourt.has(row.playerId));
}

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
