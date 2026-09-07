/**
 * **The relaxation ladder, as the pool draws it** — which offers are controls, which are
 * sentences, and when there is nothing left to say but the reach.
 *
 * The ladder ships on the pool and on **no other screen**
 * ([#223](https://github.com/Raketa02/Raketa/issues/223)). Every other thin-result state in
 * the specs pointed the player at a settings screen, which was the product being unhelpful on
 * purpose while a one-tap widening with a true count sat on the same screen; the court states
 * its shortfall in the four `UnfilledReason` codes and routes its remedy here, and the deck
 * keeps the one *widen in You* sentence that is honest because nothing else reaches it.
 *
 * ## Three shapes, and the two empties the wire keeps apart
 *
 * | | |
 * | --- | --- |
 * | `silent` | `rung_offers` is `null` — nobody needed them, and **the list is the answer** |
 * | `offered` | priced rungs to draw: the ones worth taking, and the ones that are only a fact |
 * | `exhausted` | nothing left to move, and the reach is stated instead of offered |
 *
 * `null` and `[]` are **different answers** and the falsifier is one against the other:
 * `null` is *the list cleared five*, `[]` is *they were computed and there is nothing left*.
 * That is why `null` with no rows resolves to `exhausted` rather than to `silent` — it is a
 * contradiction on the wire, and a blank screen is the one answer that is never honest.
 *
 * ## A rung priced at nobody is a statement, never a control
 *
 * ADR-0099 §5 says the count is printed on the button. This is its one narrow amendment: a
 * button that provably returns an empty list is a control lying about being useful. The count
 * still prints — that record's own *"widening to 20 km would still find nobody is the honest
 * empty state said in a number"*, said in a sentence instead of a tap.
 *
 * ## `radius_clamp` is not a gate on the offers, and reading it as one deletes real widenings
 *
 * The bit says *a widening offer hit the profile slider's own ceiling* — **not** *the searcher
 * is at the ceiling*. `radius_ladder` sets it whenever a multiplier overshoots and then
 * **clamps that rung down to 50 km and offers it anyway**: a searcher at 26 km is offered 39
 * and 50 with the bit set, and both are real rungs priced by a genuine re-run. Filtering them
 * out on the bit would take a one-tap widening with a true count away from exactly the player
 * it was built for — which is the failure the ladder exists to prevent, arriving from the gate
 * that was supposed to prevent it.
 *
 * So this function does not read the clamp at all. **What the bit gates is a sentence**: when
 * nothing is left to offer, the copy states the reach as a fact instead of asking for a
 * widening the player cannot give ([#223](https://github.com/Raketa02/Raketa/issues/223) §5,
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §17), and that is
 * `components/poolPresentation.ts`'s `terminalReachLine`. `RadiusLadder`'s own docstring is
 * the other half of the reading: *"clamped is recorded even when it left no rung standing —
 * that is exactly the searcher already at the maximum, and counting them is the whole point of
 * the bit."* **Left no rung standing** is the case the sentence is for; it is not the only case
 * the bit is set in.
 *
 * ## What is deliberately not decided here
 *
 * **Whether the climb may go further.** One climb per search screen, and *"the bound is
 * enforced in `_ladder`, not in the client — a rule in TypeScript is a rule a second client
 * gets wrong"*. A search that took a rung is offered none, and its list is `[]` rather than
 * `null`; this file sees that as any other terminal answer and needs no memory of it.
 *
 * **The words.** The sentences are `components/poolPresentation.ts`', including the three
 * different reasons a terminal ladder has for being terminal — which are a matter of what to
 * say and not of what to draw.
 */

import type { RungOffer } from './candidate';

/**
 * What the pool draws beneath its rows.
 *
 * `offered` carries both lists because the split is the whole decision: a control is a rung
 * with somebody behind it, and a statement is a rung whose count is a fact rather than an act.
 * Either may be empty; both empty is not representable, because that is `exhausted`.
 */
export type PoolLadder =
  /** The list is the answer. Nothing is drawn — not an empty block, and not a heading. */
  | { readonly kind: 'silent' }
  | {
      readonly kind: 'offered';
      /** Rungs worth taking, in the engine's own recommended order. Nothing here sorts. */
      readonly controls: readonly RungOffer[];
      /** Rungs priced at nobody — the reach, said as a fact. */
      readonly statements: readonly RungOffer[];
    }
  /** No ask left to move for this search. The reach is stated and no control is drawn. */
  | { readonly kind: 'exhausted' };

export function poolLadder(pool: {
  /** How many rows the answer carried — the shown rows, never a population. */
  readonly rows: number;
  readonly offers: readonly RungOffer[] | null;
}): PoolLadder {
  if (pool.offers === null) return pool.rows > 0 ? { kind: 'silent' } : { kind: 'exhausted' };
  if (pool.offers.length === 0) return { kind: 'exhausted' };

  return {
    kind: 'offered',
    controls: pool.offers.filter((offer) => offer.candidatesAboveFloor > 0),
    statements: pool.offers.filter((offer) => offer.candidatesAboveFloor === 0),
  };
}
