/**
 * **What an answer says back to the player — on the deck's card and on the radar's sheet.**
 *
 * The two surfaces give the same two answers through the same routes
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4), and everything the *press* says is the same too: the ceiling withheld with the deck's
 * sentence, the pass spoken, the yes's reply turned into a spoken line or the one toast. The
 * cache side of a yes is one function already (`hooks/useDeck`'s `settleYes`); this is the
 * press side, spelled once so the deck and the radar cannot drift about who may fly or what is
 * said when they do. The decision is `domain/yesBudget`'s and the words are
 * `deckPresentation`'s; what is here is only the one place each is applied.
 */

import { showToast } from '@/shared/store/toast.store';
import { announce } from '@/shared/ui';

import type { InclusionReason } from '../domain/vocabulary';
import { yesWithheld } from '../domain/yesBudget';

import { passedAnnouncement, yesOutcome } from './deckPresentation';
import { CAP_REACHED_SENTENCE } from './playErrorMessage';

/**
 * Whether a yes on this person is withheld at the ceiling — and if so, the sentence is said.
 *
 * `true` is *nothing is sent*: no yeses to give, on somebody who carries no `inclusion_reason`.
 * A liker's yes goes whatever the count, because a yes that closes a mutual is never
 * outstanding; and the server stays the authority — a `409` is still answered as a refusal.
 */
export function withheldAtTheCap(facts: {
  readonly give: number | undefined;
  readonly inclusionReason?: InclusionReason;
}): boolean {
  if (!yesWithheld(facts)) return false;
  showToast({ message: CAP_REACHED_SENTENCE });
  return true;
}

/** A pass, spoken on the press: the card's leaving or the sheet's closing is the rest of the feedback. */
export function sayPassed(name: string): void {
  announce(passedAnnouncement(name));
}

/**
 * A yes's reply, said: a one-sided yes is spoken and not shown, a mutual naming no chat is the
 * one toast, and a mutual naming a challenge is the yes screen — pushed by the mutation's own
 * success and not from here, so this says nothing for it.
 */
export function sayYesOutcome(
  name: string,
  reply: { readonly mutual: boolean; readonly challengeId: string | null },
): void {
  const outcome = yesOutcome(name, reply);
  if (outcome.kind === 'announce') announce(outcome.message);
  if (outcome.kind === 'toast') showToast({ message: outcome.message, tone: outcome.tone });
}
