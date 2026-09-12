/**
 * **The screen you answer on** — one challenge read richly, and the acts on it.
 *
 * | | |
 * | --- | --- |
 * | `useChallenge` | `GET /challenges/{id}` — the arrangement, the people and the pairing |
 * | `useAnswerSeat` | `POST …/accept` and `…/decline` — **pending, never optimistic** |
 * | `useInviteSeats` | `POST …/seats` — ⚡'s send, from the builder this screen pushes |
 * | `useWithdrawChallenge` | `POST …/withdrawal` — the organiser's, and the only end a half-built court has |
 * | `useLeaveGame` | `POST …/departure` — any player's, from the **game** screen, while the moment is ahead |
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
 * **And the conversation, which is the third**: the first acceptance opens a room and every
 * later one grows it. `features/conversations/` arrived with
 * [#363](https://github.com/Raketa02/Raketa/issues/363) and the invalidation it needed was the
 * one line this file said it would be rather than a second mechanism — the withdraw below takes
 * the same line in the opposite direction, because a destroyed room is a list that has changed
 * for a reason no reply describes.
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

import { conversationKeys } from '@/features/conversations/types';
import { gameKeys } from '@/features/games/types';
import { planKeys } from '@/features/plans/types';

import type { AnsweredChallenge, ChallengeDetail } from '../domain/challengeDetail';
import { redrawnFrom } from '../domain/challengeDetail';
import { answerSeat, type AnswerSeatAsk } from '../use-cases/answerSeat';
import { inviteSeats, type InviteSeatsAsk } from '../use-cases/inviteSeats';
import { leaveGame } from '../use-cases/leaveGame';
import { readChallenge } from '../use-cases/readChallenge';
import { withdrawChallenge } from '../use-cases/withdrawChallenge';

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
      // The room the **first** acceptance opens, and the one every later acceptance grows. It
      // is a list this response says nothing about, so it is fetched rather than patched.
      void client.invalidateQueries({ queryKey: conversationKeys.list() });
    },
  });
}

/**
 * **⚡'s send** — the open seats offered, and the challenge as it now stands.
 *
 * `POST /challenges/{id}/seats`, called from the builder this screen pushed. It is the second
 * act in the feature that reaches other people and it takes the first's posture whole: pending
 * never optimistic, `CHALLENGE_MUTATION_OPTIONS` spread whole, and no `Idempotency-Key` — the
 * open-challenge rule does not expire and a key does.
 *
 * **The detail is invalidated rather than redrawn, and that is the one place this differs from
 * the two answers.** The reply is `ChallengeSchema` and carries no `read_at`, and what the
 * challenge screen draws next is *"the new seats, their fresh deadlines, and a standing that may
 * now be awaiting answers again"* — durations, all of them folded against an instant. Writing the
 * reply in would state a fresh 24 hours against the moment the screen was **opened**, which is
 * however long the builder session took ago. `redrawnFrom` refuses to move `readAt` for exactly
 * that reason; here the honest answer is the read the screen is already mounted for, which
 * `staleTime: 0` makes immediate.
 */
export function useInviteSeats() {
  const client = useQueryClient();

  return useMutation<AnsweredChallenge, AppError, InviteSeatsAsk>({
    mutationFn: inviteSeats,
    ...CHALLENGE_MUTATION_OPTIONS,
    onSuccess: (_filled, ask) => {
      void client.invalidateQueries({ queryKey: challengeKeys.detail(ask.challengeId) });
      void client.invalidateQueries({ queryKey: challengeKeys.list() });
    },
  });
}

/**
 * **The withdraw** — the one act on this screen that ends something rather than answering it.
 *
 * Pending, never optimistic: the route returns the challenge as it now stands at `WITHDRAWN`, so
 * the screen redraws from the reply exactly as the two answers do, and `redrawnFrom` drops the
 * card block by ADR-0143 §8's rule rather than by a round trip.
 *
 * **The conversation is gone, not delisted**, so the Chats list is **invalidated rather than
 * patched** ([ADR-0142](../../../../../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)):
 * there is nothing in this reply about a room, and a client that removed the row itself would be
 * asserting a deletion it was not told about. The same argument the accept above makes in the
 * other direction.
 */
export function useWithdrawChallenge() {
  const client = useQueryClient();

  return useMutation<AnsweredChallenge, AppError, string>({
    mutationFn: withdrawChallenge,
    ...CHALLENGE_MUTATION_OPTIONS,
    onSuccess: (withdrawn, challengeId) => {
      client.setQueryData<ChallengeDetail | undefined>(challengeKeys.detail(challengeId), (held) =>
        held === undefined ? held : redrawnFrom(held, withdrawn),
      );

      void client.invalidateQueries({ queryKey: challengeKeys.list() });
      void client.invalidateQueries({ queryKey: conversationKeys.list() });
    },
  });
}

/**
 * ***Leave this game*** — the departure, and the one act in this feature pressed on a screen that
 * is not this feature's ([ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)).
 *
 * The act lands on the challenge — that is where the seat reopens — and it is reached from the
 * game, which carries its `challengeId`; so the hook is here, behind the `LeaveGame` control that
 * `types.ts` exports, and the control is composed onto the game screen by `features/plans` the way
 * `useChatDoors` is.
 *
 * **Pending, never optimistic**, and `CHALLENGE_MUTATION_OPTIONS` spread whole: a departure is
 * dated exactly, and the moment guard is read against the tap — one queued for a reconnect could
 * land past the agreed moment as a refusal nobody was there to read.
 *
 * **What lands is a redraw for the challenge screen and a re-read for everything else.** The
 * reply is the challenge as it now stands with the reader's seat `LEFT`, written into the detail
 * as the withdraw's is. The game, its plan and its room are **lists this reply says nothing
 * about** — the leaver's rail drops the card, their plans list drops the row, their inbox drops
 * the room — so all three are invalidated rather than patched: the card is gone from the rail
 * because the server no longer lists it, not because the client removed it. `planKeys` is read
 * from `features/plans` for this one line, because a hook that declares its cache effect
 * declares all of it.
 */
export function useLeaveGame() {
  const client = useQueryClient();

  return useMutation<AnsweredChallenge, AppError, string>({
    mutationFn: leaveGame,
    ...CHALLENGE_MUTATION_OPTIONS,
    onSuccess: (left, challengeId) => {
      client.setQueryData<ChallengeDetail | undefined>(challengeKeys.detail(challengeId), (held) =>
        held === undefined ? held : redrawnFrom(held, left),
      );

      void client.invalidateQueries({ queryKey: challengeKeys.list() });
      void client.invalidateQueries({ queryKey: gameKeys.list() });
      void client.invalidateQueries({ queryKey: planKeys.list() });
      void client.invalidateQueries({ queryKey: conversationKeys.list() });
    },
  });
}
