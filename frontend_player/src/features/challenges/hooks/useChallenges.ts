/**
 * The send, and the one read a refused send makes.
 *
 * | | |
 * | --- | --- |
 * | `useSendChallenge` | `POST /challenges` — **pending, never optimistic**, and the one act in the app that fails offline rather than pausing |
 * | `useOpenPair` | `GET /challenges` — asked **only after** `open_challenge_stands`, to name the pair the refusal would not |
 *
 * ## Pending, not optimistic — and the *or* dissolves rather than being chosen between
 *
 * Part 7 says avoid optimistic where the response touches several entities, where rejection is
 * not rare, and where a rollback would confuse. A send is all three: it reaches four people, its
 * refusal is a **designed-in five-gate check** rather than an unlikely event, and
 * [#227](https://github.com/Raketa02/Raketa/issues/227) made success **replace the whole
 * stack** — so a rolled-back send has nowhere to return *to*. Nothing is rolled forward, and
 * therefore nothing needs rolling back: the control is busy, the stack is replaced on success
 * only, and the toast fires after the reply.
 *
 * ## The cache effect is an invalidation and not a write
 *
 * The answer is one id. There is no challenge in it to write into the list, and the list is not
 * held by anybody at the moment of the send — the stack is about to be replaced. So the entry is
 * **invalidated** rather than updated, which is Part 7's *"mutations declare their cache
 * effect"* answered honestly: the next reader fetches, and a hand-assembled row would be this
 * client guessing at a standing the server derives.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import { pairAlreadyPlaying, type Challenge } from '../domain/challenge';
import { readChallenges } from '../use-cases/readChallenges';
import { sendChallenge, type SendAsk, type SentChallenge } from '../use-cases/sendChallenge';

import { challengeKeys } from './challengeKeys';
import { SEND_MUTATION_OPTIONS } from './sendOptions';

/**
 * ⚡ becomes a challenge.
 *
 * `SEND_MUTATION_OPTIONS` is spread whole rather than partly: it is one decision about one act,
 * and a call site that copied half of it would leave the paused queue reachable, which is the
 * thing the override exists to close.
 *
 * No `retry`. The app-wide mutation default is already `retry: false`, and a send is the one
 * request in this app where an automatic repeat would ask four people twice — refused by the
 * pair rule the second time, which is correct and is still a round trip nobody pressed for.
 */
export function useSendChallenge() {
  const client = useQueryClient();

  return useMutation<SentChallenge, AppError, SendAsk>({
    mutationFn: sendChallenge,
    ...SEND_MUTATION_OPTIONS,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: challengeKeys.list() });
    },
  });
}

/**
 * **Who on this court you already have a game with** — `undefined` until there is an answer, and
 * `undefined` again when the game in the way is not one of yours.
 *
 * `enabled` is the refusal, and it is the whole reason this is a query with a switch rather than
 * a read the screen makes on arrival: a court is built, looked at and sent from without anybody
 * needing to know what else the organiser has open, and asking on every visit would be a request
 * per builder session to answer a question almost none of them ask.
 *
 * The invitees are **not** in the key. This is one list either way, and keying it per court would
 * mint an entry per line-up for one answer — the derivation over it is free.
 *
 * **It answers a player id and never a name.** Turning one into words needs the handle, which is
 * the *court's* to read off the search it was built from — this feature has never seen a
 * nickname and must not learn to guess one.
 *
 * `undefined` while the answer is on its way, and `undefined` again when there is nobody in it
 * to name. The two are deliberately not told apart: the sentence the screen writes without a
 * name is true in both, and a third state would be a spinner over a refusal that has already
 * been stated.
 */
export function useOpenPair(invitees: readonly string[], enabled: boolean): string | undefined {
  const { data } = useQuery<readonly Challenge[], AppError>({
    queryKey: challengeKeys.list(),
    queryFn: ({ signal }) => readChallenges({ signal }),
    enabled,
    /**
     * **Never served from cache**, which is the one thing this read cannot afford.
     *
     * The app-wide default is thirty seconds, and it is right for almost everything — but this
     * list is read *after a refusal*, to name a person, and the second refusal of a session
     * would land inside that window and name whoever the first one named. A challenge answered
     * in between would make that the **wrong** person, in the one sentence in the feature that
     * says somebody's handle out loud.
     *
     * Zero rather than an invalidation at the refusal, because the two are the same instruction
     * and only one of them is stated where the read is: an `invalidateQueries` on the far side
     * is a rule the next caller of this hook does not inherit.
     */
    staleTime: 0,
  });

  return data === undefined ? undefined : pairAlreadyPlaying(data, invitees);
}
