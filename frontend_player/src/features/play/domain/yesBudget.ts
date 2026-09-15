/**
 * *N yeses to give* — and the one place the client pre-empts the server's cap.
 *
 * ## The number is two figures off the wire and one subtraction here
 *
 * `GET /interest` carries, per sport, how many yeses are outstanding and the cap in force —
 * *"before you are near either — a cap you cannot see is a refusal you cannot predict"*. The
 * counter prints the difference ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §5), and the subtraction is the one piece of arithmetic this app does over those two
 * numbers: the cap is ruleset configuration and is never hardcoded, the count moves on a tap's
 * own response, and neither is derived from a list.
 *
 * ## At the ceiling, a stranger's card settles and a liker's card flies
 *
 * With no yeses to give, a yes on somebody who has not said yes to the viewer would be refused
 * — so the card does not fly, and a toast says the ceiling. A yes on somebody who **has** said
 * yes is different in kind: it closes a mutual, is answered the instant it is written, and gives
 * the slot straight back, so it is never outstanding and the server's cap check exempts it
 * (ADR-0169 §3). The client reads the same two facts it already holds — the count, and the
 * card's `inclusion_reason` — and pre-empts the one refusal it can predict. **The server stays
 * the authority**: a `409` still returns the card, so this rule is a courtesy and never the
 * correctness.
 *
 * It is a `domain/` rule for `onCourtMark`'s reason: there are two things to be wrong about —
 * which way the exemption runs, and what an absent count means — and a component holding
 * `give === 0 && !liker` at one site is one refactor from withholding a mutual.
 */

import type { InclusionReason } from './vocabulary';

/**
 * Whether a card's person is a **liker** — somebody whose live yes towards the viewer admitted
 * them. Spelled against the one admitting code rather than as *any* inclusion reason, so a
 * second admitting code — somebody admitted for another reason entirely — arrives here as a
 * stranger to the cap and to the chip, which is what it would be.
 */
export function isLiker(card: { readonly inclusionReason?: InclusionReason }): boolean {
  return card.inclusionReason === 'INTEREST_LIFT';
}

/** Where one sport stands against its cap, as `GET /interest` says it — and how long a yes lives. */
export interface InterestStanding {
  readonly outstanding: number;
  readonly cap: number;
}

/**
 * How many more yeses this sport will take — the cap less the outstanding, floored at nought.
 *
 * The floor is for a cap that has come down between releases under a standing count: a
 * negative number of yeses to give is not a thing a pill can print.
 */
export function yesesToGive(standing: InterestStanding): number {
  return Math.max(0, standing.cap - standing.outstanding);
}

/**
 * Whether a yes on this card is withheld before it is sent — see the module note.
 *
 * `give` is `undefined` until the interest read has landed, and **nothing is withheld on an
 * absent count**: the client pre-empts what it can read, and where it can read nothing the
 * server answers, as it always did.
 */
export function yesWithheld(facts: {
  readonly give: number | undefined;
  /** Why they are on the deck at all — a liker carries `INTEREST_LIFT`. Omitted for a stranger. */
  readonly inclusionReason?: InclusionReason;
}): boolean {
  if (facts.give === undefined || facts.give > 0) return false;
  return !isLiker(facts);
}
