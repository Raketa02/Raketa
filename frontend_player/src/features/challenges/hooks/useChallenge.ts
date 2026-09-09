/**
 * **The screen you answer on** — one challenge read richly, and the one act on it.
 *
 * | | |
 * | --- | --- |
 * | `useChallenge` | `GET /challenges/{id}` — the arrangement, the people and the pairing |
 * | `useAnswerSeat` | `POST …/accept` and `…/decline` — **pending, never optimistic** |
 *
 * ## The offer may expire under the finger, and it is let to
 *
 * `staleTime: 0` with the app's own `refetchOnWindowFocus`, so a refetch can redraw **I'm in**
 * away while the player is looking at it. Play pins its ranked lists and **the reason does not
 * transfer**: a pinned pool *is* the record, where a challenge's standing is derived against a
 * clock and genuinely goes false while you look at it. **A mis-tap prevented beats a mis-tap
 * refused** ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md)
 * §2.4).
 *
 * What that costs is discharged one file over rather than here: **an affordance is never removed
 * without the space saying what happened to it**, so the screen replaces the buttons with the
 * sentence the new standing derives and never with nothing.
 *
 * ## Pending, never optimistic — and the reply is the redraw
 *
 * Part 7 says avoid optimistic where the response touches several entities and where rejection
 * is not rare. An accept is both: the one that fills the last seat opens a **game** and a
 * **conversation** in the same transaction, and the refusals here are two designed-in states of
 * a clock rather than unlikely events. So nothing is rolled forward and nothing needs rolling
 * back — the control is busy, and what lands is written in.
 *
 * **What lands is the server's own derived standing**, so writing it into the cache is not
 * guessing: `redrawnFrom` folds it onto the detail the screen holds and keeps the card block,
 * which ADR-0143 §8 settles in as many words. A refetch to learn what the reply already said
 * would be a request asking a question this client can answer.
 *
 * ## The neighbours are fetched, and they are fetched rather than patched
 *
 * An accept that fills the last seat opens a game and a conversation **in caches this response
 * says nothing about**: `GET /games` gains a row and the Chats list's sections both move. There
 * is nothing in the reply to write into either, so both **lists** are invalidated — Part 7's *mutations
 * declare their cache effect* answered honestly, where a hand-assembled row would be this client
 * inventing a game the server has not described to it.
 *
 * The conversation has no cache to invalidate yet: `features/conversations/` arrives with
 * [#363](https://github.com/Raketa02/Raketa/issues/363) and
 * [#364](https://github.com/Raketa02/Raketa/issues/364), and the invalidation it will need is
 * this one line longer rather than a second mechanism.
 *
 * ## The retry that is not written here, and why it is not
 *
 * The app-wide mutation default already refuses one, and `challengeMutationOptions.ts` records
 * why it is not restated at a call site: *a second place for one decision to be changed*. It is
 * worth knowing what that default is buying on this route, though — an answer is **not
 * idempotent, deliberately**, because *yes* after *no* is a different answer and not a repeat of
 * one, so an automatic second attempt would be the app answering for the player.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import { gameKeys } from '@/features/games/types';

import type { AnsweredChallenge, ChallengeDetail } from '../domain/challengeDetail';
import { redrawnFrom } from '../domain/challengeDetail';
import { answerSeat, type AnswerSeatAsk } from '../use-cases/answerSeat';
import { readChallenge } from '../use-cases/readChallenge';

import { challengeKeys } from './challengeKeys';
import { CHALLENGE_MUTATION_OPTIONS } from './challengeMutationOptions';

/**
 * One challenge, richly.
 *
 * `undefined` data covers two states the screen tells apart by `error`: still coming, and a
 * record whose sport this build cannot name. The `404` arrives as an error like any other, and
 * the screen says the one thing that is true of all three — *no challenge of yours has this
 * address*.
 */
export function useChallenge(challengeId: string) {
  return useQuery<ChallengeDetail | undefined, AppError>({
    queryKey: challengeKeys.detail(challengeId),
    queryFn: ({ signal }) => readChallenge(challengeId, { signal }),
    staleTime: 0,
  });
}

/**
 * `I'm in` and `Not this time`.
 *
 * `CHALLENGE_MUTATION_OPTIONS` is spread whole rather than partly: it is one decision about every
 * act in this feature — **nothing in `challenges` is sent for you later** — and a call site that
 * copied half of it would leave the paused queue reachable, which is the thing the override
 * exists to close. An answer's meaning is fixed by the moment it is tapped: one deferred to the
 * next reconnect can land past a deadline as silence, or arrange a game at a moment nobody was
 * present for.
 */
export function useAnswerSeat() {
  const client = useQueryClient();

  return useMutation<AnsweredChallenge, AppError, AnswerSeatAsk>({
    mutationFn: answerSeat,
    ...CHALLENGE_MUTATION_OPTIONS,
    onSuccess: (answered, ask) => {
      const key = challengeKeys.detail(ask.challengeId);

      // The redraw. `undefined` is a detail this screen never held — the merge has nothing to
      // fold onto, and the read that fills the key is already on its way.
      client.setQueryData<ChallengeDetail | undefined>(key, (held) =>
        held === undefined ? held : redrawnFrom(held, answered),
      );

      // The neighbours, and **the list rather than `all`**: `all` is a prefix that matches this
      // entry too, and invalidating a mounted query refetches it — which would send the request
      // the redraw above exists to make unnecessary, and would drop the card block by a round
      // trip instead of by ADR-0143 §8's rule.
      void client.invalidateQueries({ queryKey: challengeKeys.list() });
      void client.invalidateQueries({ queryKey: gameKeys.all });
    },
  });
}
