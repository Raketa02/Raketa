/**
 * **One decision, two answers** — and one use-case, because they are one act with two values.
 *
 * `I'm in` and `Not this time` are the same seat answered, routed by what was answered: two
 * hooks over two use-cases would be two places for the cache effect, the refusal arms and the
 * *never sent for you later* rule to be stated, and the first one to be forgotten would be the
 * one nobody was looking at.
 *
 * **A lapse is not one of these.** Silence past your day is a fact the platform records and
 * neither of these produces — the `answers challenges` strand needs the denominator, and a
 * client that spelled a third value here would be inviting somebody to file silence as a
 * judgement.
 *
 * The reply is `ChallengeSchema`, which is the server's **derived** standing rather than an
 * acknowledgement, so it is the redraw. Folding it onto the detail the screen holds is
 * `redrawnFrom`'s rule and not this file's.
 */

import { postAccept, postDecline } from '../api/challengesApi';
import type { AnsweredChallenge } from '../domain/challengeDetail';
import { toAnsweredChallenge } from '../mappers/challengeDetailMappers';

/** What the player said. Named for the answers rather than for the routes that carry them. */
export type SeatAnswerAct = 'accept' | 'decline';

export interface AnswerSeatAsk {
  readonly challengeId: string;
  readonly act: SeatAnswerAct;
}

export async function answerSeat(ask: AnswerSeatAsk): Promise<AnsweredChallenge> {
  const answered =
    ask.act === 'accept' ? await postAccept(ask.challengeId) : await postDecline(ask.challengeId);

  return toAnsweredChallenge(answered);
}
