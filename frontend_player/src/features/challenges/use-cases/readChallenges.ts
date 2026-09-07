/**
 * **Your own challenges** — read for one reason today, and it is the reason the refusal names.
 *
 * `open_challenge_stands` says *"two people on this court already have a game between them, in
 * any sport"* and says nothing else, because a refusal has nowhere typed to put a payload and
 * a name in an error message is a disclosure route. So the client re-reads the list that was
 * **always its own**: #222 puts that gate on the *embarrassment* side rather than the safety
 * side, so naming the pair here costs nothing ADR-0095 protects.
 *
 * The **rule** it is read against is `domain/challenge.ts`'s. This is only the fetch, which is
 * the whole of what a use-case owes when the domain owns the question.
 */

import { getChallenges, type Cancellable } from '../api/challengesApi';
import type { Challenge } from '../domain/challenge';
import { toChallenges } from '../mappers/challengeMappers';

export async function readChallenges({ signal }: Cancellable = {}): Promise<readonly Challenge[]> {
  return toChallenges(await getChallenges({ signal }));
}
