/**
 * **The standing relation** between the reader and a person on the radar — which foot the
 * record sheet draws for them
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4, [`the-radar.md`](../../../../../docs/specs/matchmaking/the-radar.md) §5).
 *
 * The sheet reached from a radar card gains a foot the deck's *i* never has: *Not today* and
 * *Let's play*, or, where a relation already stands, what it is. Five facts reach the foot from
 * four places — the row's own admitting code, the reader's outgoing and mutual lists, and the
 * reader's challenge list — and more than one can be true at once. **The precedence is the whole
 * of this rule**, and it is a `domain/` rule for `yesBudget`'s reason: a component holding four
 * `if`s at one site is one refactor from drawing two buttons over a match.
 *
 * ## The order, and why
 *
 * 1. **Matched** — their yes came back. The one relation the reader has *earned* something by:
 *    the chat. Over a court, because a mutual-born court is the ordinary case and *You're
 *    matched* with the door is what the ticket draws for it; the court's own line is one tap
 *    away in that chat.
 * 2. **A court** — a challenge or game the two share, live or behind them. Over either yes,
 *    because the deck's cool-off holds such a pair out of the deck for the same reason: *a
 *    rematch is arranged in the chat the two already have* (ADR-0169 §6), and a *Let's play*
 *    on somebody you are already on a court with is a yes the server answers with no game.
 * 3. **A liker** — the row's `inclusion_reason`, the other person's decision. *Wants to play
 *    you* above the two buttons, so the chip's promise is findable on a surface with no order
 *    (§4). Over the reader's own yes where both are read true, for the builder card's reason:
 *    both facts true is a mutual the lists have not caught up with, and the other person's
 *    decision is the one the reader did not already know.
 * 4. **Said yes** — the reader's own live yes. *You said yes* beside *Not today*: a second yes
 *    changes nothing on the wire, so the one button left is the pass. It does not take the yes
 *    back — nothing does; a yes lives its 21 days — it says *not to my deck*, which is what a
 *    pass has always meant (ADR-0128 §1).
 * 5. **Open** — the two buttons. A *not today* the reader gave earlier lands here too: **no
 *    route anywhere returns a pass**, so the client cannot tell a stranger from somebody passed
 *    on, and the spec asks for the same two buttons either way — *Let's play* lifts the pass.
 */

import type { InclusionReason } from './vocabulary';
import { isLiker } from './yesBudget';

/**
 * The five feet, by the relation that earns each — and the court, carried on the one arm that
 * names it.
 *
 * Generic over what a court *is*, because this rule reads the challenges feature's answer
 * without knowing its shape: the fold asks only whether there is one, and hands it back on the
 * arm where the surface draws it, so no reader has to narrow a value the fold already had.
 */
export type StandingRelation<Court> =
  | { readonly kind: 'matched' }
  | { readonly kind: 'court'; readonly court: Court }
  | { readonly kind: 'liker' }
  | { readonly kind: 'said-yes' }
  | { readonly kind: 'open' };

export interface RelationFacts<Court> {
  /** Why they are on the reading at all — a liker carries `INTEREST_LIFT`. Omitted for a stranger. */
  readonly inclusionReason?: InclusionReason;
  /** The reader's own outgoing list's answer (`saidYesTo`), never this row's. */
  readonly saidYes: boolean;
  /** The reader's own mutual list's answer (`matchedWith`), never this row's. */
  readonly matched: boolean;
  /** The court the two share, as the challenges feature answers it — or nothing. */
  readonly court: Court | undefined;
}

export function standingRelation<Court>(facts: RelationFacts<Court>): StandingRelation<Court> {
  if (facts.matched) return { kind: 'matched' };
  if (facts.court !== undefined) return { kind: 'court', court: facts.court };
  if (isLiker(facts)) return { kind: 'liker' };
  if (facts.saidYes) return { kind: 'said-yes' };
  return { kind: 'open' };
}
