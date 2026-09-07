/**
 * ⚡ becomes a challenge — **the one act in this feature that reaches another person**, and the
 * last one a Play session performs.
 *
 * ## What it does not do, and why the list is the design
 *
 * It carries **no window and no duration**. The sport, the kind of evening and the week are the
 * cited search's, derived at send and recorded there; a client that sent one would be a second
 * place for the answer window to come from, and the first to go silently false the day the
 * window moves ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §14, §21).
 *
 * It carries **no seating decision beyond the one on screen**. *"The arrangement you built is
 * what is recorded, and it is what they answer — never a better one worked out afterwards"*, so
 * the court goes out exactly as the builder drew it.
 *
 * It **re-checks nothing**. Five facts are re-verified server-side in the send's own
 * transaction, because nothing in Play background-refetches and the line-up may be an hour old
 * — a client-side pre-check would be a fifth reading of a rule that must not be stale, taken
 * from the one source that is.
 *
 * ## The answer is an id, and the screen keeps none of it
 *
 * On success the stack is **replaced** and the Play session ends, so there is nothing left
 * holding a challenge id: the confirmation is a toast, and the challenge is read back off
 * `GET /challenges` like anybody else's. The id crosses anyway because the route returns it and
 * a use-case that dropped an answer would be inventing a `204` the contract does not have.
 */

import { postChallenge } from '../api/challengesApi';
import { toSendChallengeRequest, type ProposedCourt } from '../mappers/challengeMappers';

/**
 * What the send is pressed with: **the court, and the search it was built from.**
 *
 * `searchId` is the Origin key — every invitee must have appeared in it, and each seat cites
 * where they sat. It is the line-up's own origin rather than whatever the screen arrived on,
 * because ⚡ mints a search and re-binds the line-up to it.
 */
export interface SendAsk {
  readonly searchId: string;
  /** Seat order, your own seat included, `undefined` where nobody is sitting. */
  readonly court: ProposedCourt;
}

/** The challenge that now stands. */
export interface SentChallenge {
  readonly challengeId: string;
}

export async function sendChallenge(ask: SendAsk): Promise<SentChallenge> {
  const response = await postChallenge(toSendChallengeRequest(ask));

  return { challengeId: response.challenge_id };
}
