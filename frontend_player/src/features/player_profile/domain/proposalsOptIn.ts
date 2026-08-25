/**
 * The **Proposals opt-in**'s rule, which is one sentence long: *an answer that has not been
 * given is not an answer.*
 *
 * The opt-in is the only field of the six with **no default in either direction**
 * (`CONTEXT.md` — *Skipping is not consent*). Every other step either ships with a sensible
 * value or has a genuinely empty answer: a blank week means no preference, no photos is a
 * complete reply, and the radius opens at the served default. This one has neither. So the
 * absence has to be a state a caller can see and be refused on, rather than an `undefined`
 * that the first `if` mistakes for a no.
 *
 * ## Why the standing is a shape rather than a boolean
 *
 * `boolean | undefined` is exactly the type that lets *unanswered* fall through to *no*:
 * one `if (accepted)` and a player who was never asked has been recorded as refusing. The
 * three states are spelled out so that reading one of them is a decision rather than a
 * coincidence — the same argument `socialTagSelection`'s standing makes about a floor.
 *
 * ## No is a whole answer
 *
 * `mayFinish` is deliberately blind to *which* answer was given. A gate that opened only on
 * yes would be the product withholding the rest of itself until the player consented, and
 * a player who declines has finished this step exactly as completely as one who accepts.
 * That is a rule worth stating once, in a file with no renderer, rather than living inside
 * a `disabled` prop where the difference between *unanswered* and *declined* is one typo.
 *
 * The words the answer was given against travel with it in `ProposalsOptIn` itself, so
 * there is no arrangement of these functions that can produce an answer without them.
 */

import type { ProposalsOptIn } from './ProfileDraft';

/**
 * Where the step stands: not asked yet, or asked and answered one way or the other.
 *
 * The answered arm carries the answer rather than being two arms, because everything that
 * reads it — the two controls' selected state, the finish, and the commit — cares about
 * *yes or no* only after it has established that there is an answer at all.
 */
export type ProposalsOptInStanding =
  { readonly kind: 'unanswered' } | { readonly kind: 'answered'; readonly accepted: boolean };

export function optInStanding(optIn: ProposalsOptIn | undefined): ProposalsOptInStanding {
  return optIn === undefined
    ? { kind: 'unanswered' }
    : { kind: 'answered', accepted: optIn.accepted };
}

/**
 * Whether the part may be finished from here.
 *
 * **Either answer, and nothing else.** There is no skip, no dismiss and no decide-later
 * anywhere on this step, because a player who passed through one of those would be neither
 * opted in nor opted out — and somebody downstream would then have to guess, which is the
 * guess consent exists to make unnecessary.
 */
export function mayFinish(standing: ProposalsOptInStanding): boolean {
  return standing.kind === 'answered';
}
