/**
 * **The pool's order** — which chips the row draws, what each of them does to rows the screen
 * already holds, and the two things this file decides that are not comparators at all.
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
 *
 * ## A pin is not a bonus — and this is the distinction to read before deleting one
 *
 * §C5 specified the Best-fit comparator as *"the fit score plus **12** for anyone who said yes
 * to you in Match me"*, and [#231](https://github.com/Raketa02/Raketa/issues/231) struck it:
 * the server has **already** lifted those people, in the engine, as an *admission* rather than
 * a bonus, so adding twelve here would score the wire's own ranking a second time.
 * `PoolScreen`'s module note keeps that refusal in writing, and it still stands.
 *
 * **The pin below is the opposite move, and every difference is load-bearing.** A bonus is
 * arithmetic on a published figure — it changes what *best* means, silently, on a number the
 * card is printing two lines away, and it survives every re-sort because it has become part of
 * the score. A pin is a **position**: it touches no number, it is visible and named on the card
 * it moved (the tag beside the handle says *why* that row is first), and it exists only in the
 * order the rows arrived in — the moment the player asks for closest, evenest or most reliable,
 * the pinned row **drops into its honest place** and the tag travels down with it.
 *
 * So the falsifier is *what does the printed Fit say*. Under the `+12`, a 41 sorted above an
 * 88 and printed 41, which is the ranking disagreeing with itself. Under the pin, a 41 sorts
 * first, prints 41, and says *Wants to play you* — which is a different claim, made out loud.
 * A reader who arrives here on the trail of #231 is looking at the right file and the wrong
 * mechanism ([#310](https://github.com/Raketa02/Raketa/issues/310)).
 *
 * ## *Best fit* is a sort, and never a filter
 *
 * Written down because the number invites the other reading: the fit pill turns coral at ✦ ≥
 * 90 ([7.10](../../../../docs/design-system.md#710-the-fit-pill)), and a threshold on screen is
 * one somebody eventually applies to the list. `BEST_FIT` **hides nobody**. It puts the highest
 * number first and leaves every lower one on the list, in order, exactly as the other three
 * orderings do — this screen's job is the whole shortlist, and the ladder underneath it is what
 * answers a list that is genuinely short.
 */

import type { Candidate } from './candidate';
import { SORT_OPTIONS, type InclusionReason, type SortOption } from './vocabulary';

type Comparator = (one: Candidate, other: Candidate) => number;

/**
 * How each sort orders rows already held — and `undefined` where this build cannot.
 *
 * Exhaustive by type over `SortOption`, which is what makes the day a sort becomes offerable
 * a change to this one table.
 */
const COMPARATOR: Readonly<Record<SortOption, Comparator | undefined>> = {
  /**
   * The printed number, descending. Ties keep the order the engine served them in.
   *
   * **A sort and never a filter** — see the module note. It reorders the whole list and drops
   * nobody off the bottom of it.
   */
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
 * Which admitting codes are lifted to the top of the served order — **a table, not a check.**
 *
 * `INCLUSION_TAG_WORD`'s discipline for `INCLUSION_TAG_WORD`'s reason: `InclusionReason` is a
 * union of one *today*, and `inclusionReason !== undefined` would silently pin a second
 * admitting code — somebody admitted for something that is not interest at all, put at the top
 * of the list under a tag saying they want to play you. Keyed by the union, a second code
 * arrives with an answer here or does not compile.
 */
const PINS: Readonly<Record<InclusionReason, boolean>> = {
  INTEREST_LIFT: true,
};

const pinnedFirst = (rows: readonly Candidate[]): readonly Candidate[] => {
  const lifted = (row: Candidate) => row.inclusionReason !== undefined && PINS[row.inclusionReason];
  const up = rows.filter(lifted);
  // Nothing lifted is the common case and the list is returned untouched, which is `orderPool`'s
  // own shape one level down: a rule that reorders nobody hands back the array it was given.
  return up.length === 0 ? rows : [...up, ...rows.filter((row) => !lifted(row))];
};

/**
 * The rows, in the order the screen should draw them.
 *
 * `undefined` is *the order they arrived in*, which is the engine's own ranking and the pool's
 * default — **plus the pin**, which exists in that order and in no other. `Array.prototype.sort`
 * is stable, so a sort leaves rows it cannot separate exactly where the answer put them, and
 * `pinnedFirst` preserves the served order within each of its two halves for the same reason.
 *
 * **The pin releases on any chosen sort, including one that reorders nothing.** It is a property
 * of *the order the player is in*, not of whether the comparator moved anybody: `EVENEST` has a
 * word and no ordering, and a `MOST_RELIABLE` over rows the platform has watched nothing of
 * separates nobody — in both the player has still left the served order, and leaving it is the
 * whole condition. See the module note on why this is not the `+12` #231 struck.
 *
 * **`BEST_FIT` releases it too, and that is a decision with a cost worth naming.**
 * [#310](https://github.com/Raketa02/Raketa/issues/310) says the pin exists *"in the default
 * (as-served) order **only**"* and that a pinned row *"moves under **every** re-sort"*, so this
 * follows the ticket rather than the three chips its prose happens to list. What it costs is the
 * one thing this file argues for two sections up: where the server withheld `BEST_FIT` and the
 * row added it back as **the way back**, tapping it returns fit order *without* the pin, which is
 * not quite the list the player left. That is accepted rather than overlooked — the alternative
 * is a pin that survives a sort, which is the property that makes a bonus a bonus, and *the way
 * back* is a way back to an **ordering** and never to a decoration on top of one.
 */
export function orderPool(
  rows: readonly Candidate[],
  sort: SortOption | undefined,
): readonly Candidate[] {
  if (sort === undefined) return pinnedFirst(rows);
  const compare = COMPARATOR[sort];
  return compare === undefined ? rows : [...rows].sort(compare);
}

/**
 * Which orderings the coral *best match* tag exists under — **the ordering in force, never a
 * tap.**
 *
 * This is the wrinkle worth knowing. `BEST_FIT` is withheld from `sorts_available` *precisely
 * when the returned order already is best-fit order*, and `poolSortRow` adds it back only once
 * the player has left it — so on most searches there is no chip to have tapped, and a tag keyed
 * to a tap would never appear on them. Keyed to the order instead, the default draws it because
 * the default **is** fit order there, and the three orderings that are about something other
 * than the number hide it because *best match* would then be a claim about a row that is not
 * first and not marked as anything.
 */
const WEARS_BEST_MATCH: Readonly<Record<SortOption, boolean>> = {
  BEST_FIT: true,
  CLOSEST: false,
  EVENEST: false,
  MOST_RELIABLE: false,
};

/**
 * Who wears the coral tag, or **nobody** — one player id, and never two.
 *
 * @param rows the pickable rows **in the order the server served them**, which is what makes
 *   *the row the server served first* the tie-break rather than a property of whichever array a
 *   screen happened to draw.
 * @param sort what the player has selected, or `undefined` for the order they arrived in.
 *
 * **Competitive rows only reach a tag.** This function answers for whatever rows it is handed,
 * because *the highest ✦ on screen* is a fact about a list and not about a card — but the coral
 * tag lives in `IdentityRow`, which is the competitive card's alone
 * ([#309](https://github.com/Raketa02/Raketa/issues/309) left `CandidateCardSocial` untouched),
 * so a for-fun pool draws no *best match*. The pin still reorders it and the interest sentence
 * still explains why: the tag is what is missing there, not the rule.
 *
 * It names the highest row **even when that row is the pinned one**. The two tags collide on
 * one card and `candidateTag` resolves it — the volt one replaces the coral one, *"because it's
 * the stronger fact"* — and handing the coral tag to the runner-up instead would be the card
 * saying *best match* about a row that is not the best match.
 */
export function bestMatchId(
  rows: readonly Candidate[],
  sort: SortOption | undefined,
): string | undefined {
  if (sort !== undefined && !WEARS_BEST_MATCH[sort]) return undefined;

  // Strictly greater, so a tie keeps the row already held — which is the earlier one, which is
  // the one the server served first.
  const best = rows.reduce<Candidate | undefined>(
    (top, row) => (top === undefined || row.fit > top.fit ? row : top),
    undefined,
  );
  return best?.playerId;
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
