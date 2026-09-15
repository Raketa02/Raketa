/**
 * The **Proposals opt-in**'s rule, which is one sentence long: *an answer that has not been
 * given is not an answer.*
 *
 * The opt-in is the only field of the eight with **no default in either direction**
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
 * ## No is a whole answer, and the rule that says so has moved
 *
 * `mayFinish` used to live here and be blind to *which* answer was given — a gate that
 * opened only on yes would be the product withholding the rest of itself until the player
 * consented. That rule is now `profileCommit.mayFinish`, because consent stopped being the
 * only thing that can hold the finish shut: the part is also refused without a Location
 * area, and while a photo is still arriving. Neither is anything this file could have said.
 *
 * Nothing was dropped in the move. *An answer that has not been given is not an answer* is
 * one of the three `readyToCommit` reports, so the finish still opens on either answer and
 * on neither absence — and `optInStanding` below is still what the two controls draw their
 * selected state from.
 *
 * ## The words travel with the answer, and the type is what guarantees it
 *
 * There is no constructor here, deliberately. `ProposalsOptIn.copyVersion` is **required**,
 * so an answer without the wording it was given against is not a value this app can build —
 * a function wrapping an object literal would add a middle man to enforce what the type
 * already refuses. *Which* wording was shown is the screen's fact, not this file's: the
 * thing that drew the sentences is the only thing that can honestly name them.
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
