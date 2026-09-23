/**
 * **The fill's send** — the open seats offered to the four the builder just composed.
 *
 * `POST /challenges/{id}/seats` is *"the send's shape minus the mint"*
 * ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
 * §6): the challenge already holds the sport, the kind of evening and the window, so what
 * crosses is the court as it will stand and the search behind it. It re-verifies the send's five
 * facts with one changed — the open-challenge gate excepts **this** challenge and no other — and
 * either happens whole or writes nothing.
 *
 * **It is the second act in this feature that reaches other people**, and it takes the first
 * one's shape: pending never optimistic, one press, and the confirmation is the screen it pops
 * back to rather than a toast. What it does not take is the mint — nothing new is created, so
 * there is no id to hold and nothing to read back beyond the challenge, which the route returns.
 *
 * **Each newly-seated player starts their own 24 hours**, dated from this moment, and nobody
 * else's deadline moves. That is what makes the act's meaning fixed by the moment it is tapped,
 * and therefore why it fails offline rather than being sent later
 * (`challengeMutationOptions.ts`).
 *
 * `AnsweredChallenge` rather than a shape of its own: the reply is `ChallengeSchema`, exactly as
 * the two answers' is, and it is read by exactly the same fold. A second name for one wire shape
 * is how two readers of one response start disagreeing about it.
 */

import { postSeats } from '../api/challengesApi';
import type { AnsweredChallenge } from '../domain/challengeDetail';
import { toAnsweredChallenge } from '../mappers/challengeDetailMappers';
import { toFillSeatsRequest, type ProposedCourt } from '../mappers/challengeMappers';

export interface InviteSeatsAsk {
  readonly challengeId: string;
  /** The search this fill was built from — **yours, and run just now.** */
  readonly searchId: string;
  /** The **whole** court as it will stand, in the court's own order. Empty seats included. */
  readonly court: ProposedCourt;
}

export async function inviteSeats(ask: InviteSeatsAsk): Promise<AnsweredChallenge> {
  const filled = await postSeats(
    ask.challengeId,
    toFillSeatsRequest({ searchId: ask.searchId, court: ask.court }),
  );

  return toAnsweredChallenge(filled);
}
