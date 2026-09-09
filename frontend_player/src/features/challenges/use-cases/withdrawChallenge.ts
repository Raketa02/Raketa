/**
 * **The withdraw** — the one conclusion the seats cannot reach
 * ([ADR-0142](../../../../../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)).
 *
 * Every other standing is a fold of the seats and the clock; this one is an **act**, and it is
 * the exit for a line-up nobody is going to complete: somebody is in, a seat is open, nobody is
 * deciding, and nothing in the challenge will ever end it.
 *
 * **Whole-challenge, organiser only, irreversible, and in `LINE_UP_INCOMPLETE` and nowhere
 * else.** It destroys the conversation rather than delisting it — *"on a platform where standings
 * are derived and nothing else is deleted, this is the one place deletion is the honest
 * implementation"* — which is the fact the sheet in front of it exists to say out loud.
 *
 * There is no ask beyond the id: a withdraw takes no arguments because it makes no choices. The
 * reply is the challenge as it now stands at `WITHDRAWN`, which is the server's own derived
 * standing and therefore the redraw.
 */

import { postWithdrawal } from '../api/challengesApi';
import type { AnsweredChallenge } from '../domain/challengeDetail';
import { toAnsweredChallenge } from '../mappers/challengeDetailMappers';

export async function withdrawChallenge(challengeId: string): Promise<AnsweredChallenge> {
  return toAnsweredChallenge(await postWithdrawal(challengeId));
}
