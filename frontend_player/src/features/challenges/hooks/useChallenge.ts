/**
 * **The screen you answer on** — one challenge read richly, and the acts on it.
 *
 * | | |
 * | --- | --- |
 * | `useChallenge` | `GET /challenges/{id}` — the arrangement, the people and the pairing |
 * | `useAnswerSeat` | `POST …/accept` and `…/decline` — **pending, never optimistic** |
 * | `useInviteSeats` | `POST …/seats` — ⚡'s send, from the builder this screen pushes |
 * | `useWithdrawChallenge` | `POST …/withdrawal` — the organiser's, and the only end a half-built court has; **on a court that has been a game, whoever holds the exit's, and the game is called off in the act** |
 * | `useLeaveGame` | `POST …/departure` — any player's: from the **game** screen while the moment is ahead, and from a **Chats** row or the challenge screen before the court is whole (#427) |
 * | `useReReadCourtLists` | what a **refused** departure re-reads, once its words have been read — the two lists a court is drawn on |
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

import { conversationKeys, dropRoomOfChallenge } from '@/features/conversations/types';
import { gameKeys } from '@/features/games/types';
import { planKeys } from '@/features/plans/types';

import type { Challenge } from '../domain/challenge';
import type { AnsweredChallenge, ChallengeDetail } from '../domain/challengeDetail';
import { redrawnFrom, rowRedrawnFrom } from '../domain/challengeDetail';
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
      // And the court's plan, which a yes is what gives the reader a row on (ADR-0164 §3): the
      // room this lands in pins the card from its first frame, and the list held no row for a
      // court the reader was still deciding about. `planKeys` is read from `features/plans` for
      // this one line, as the leave and the withdraw already read it.
      void client.invalidateQueries({ queryKey: planKeys.list() });
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
 * **The withdraw** — the one act on the challenge screen that ends something rather than answering
 * it, and ***Call it off*** on the game screen, which is the same act on the same route
 * ([ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)).
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
 *
 * **And the game, and its plan** — since a withdraw can reach a court that has been a game and
 * call it off in the act, and neither list is in the reply. Declared here rather than at the one
 * call site that knows it was a game, because a hook that declares its cache effect declares all
 * of it (`useLeaveGame`'s own line): the game screen stays where it is and re-folds into the
 * called-off arm off the re-read, and the card shelves itself from `called_off_at`. On a court
 * that was never a game the two re-reads find nothing changed, which is the honest cost of one
 * declaration instead of two.
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
      void client.invalidateQueries({ queryKey: gameKeys.list() });
      void client.invalidateQueries({ queryKey: planKeys.list() });
    },
  });
}

/**
 * ***Leave this game*, and *Leave the game*** — the departure, met on the game screen, on a Chats
 * row, and on the challenge screen before the court is whole
 * ([ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md),
 * [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §1, §6).
 *
 * The act lands on the challenge — that is where the seat reopens — and it is reached from the
 * game, which carries its `challengeId`, from a room, which carries it too, and from the challenge
 * itself; so the hook is here, behind the `LeaveGame` control and the `DepartureDoor` that
 * `types.ts` exports, and those are composed onto the surfaces that draw them the way
 * `useChatDoors` is.
 *
 * **Pending, never optimistic**, and `CHALLENGE_MUTATION_OPTIONS` spread whole: a departure is
 * dated exactly, and the moment guard is read against the tap — one queued for a reconnect could
 * land past the agreed moment as a refusal nobody was there to read.
 *
 * **What lands is a redraw for the two rows that are the leaver's, and a re-read for everything
 * else.** The reply is the challenge as it now stands with the reader's seat `LEFT`, written into
 * the detail as the withdraw's is — and, since [#427](https://github.com/Raketa02/Raketa/issues/427),
 * into the **challenge list** too, where the inbox rule drops an own *left* at once, and taken out
 * of the **conversations list** by `dropRoomOfChallenge`, that feature's own write. Both are the
 * reply's to say: membership is the accepted seats, so a seat that reads `LEFT` *is* the reader
 * out of the room, and the withdraw's *invalidate rather than patch* argument — a reply that says
 * nothing about a room — does not hold for the one reply that does. So the leaver's two rows are
 * gone on the reply and not a round trip later. The game and its plan are still **lists this reply
 * says nothing about** — the leaver's rail drops the card, their plans list drops the row — so
 * those are invalidated rather than patched, and the two lists just written are re-read as well,
 * because the reply is one court and the lists are every court: the card is gone from the rail
 * because the server no longer lists it, not because the client removed it. `planKeys` is read from
 * `features/plans` for this one line, because a hook that declares its cache effect declares all
 * of it.
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

      // The leaver's two rows, on the reply (#427): the inbox drops an own `LEFT` at once, and
      // the room is theirs no longer because membership is the accepted seats.
      client.setQueryData<readonly Challenge[] | undefined>(challengeKeys.list(), (held) =>
        held?.map((row) => (row.challengeId === challengeId ? rowRedrawnFrom(row, left) : row)),
      );
      dropRoomOfChallenge(client, challengeId);

      void client.invalidateQueries({ queryKey: challengeKeys.list() });
      void client.invalidateQueries({ queryKey: gameKeys.list() });
      void client.invalidateQueries({ queryKey: planKeys.list() });
      void client.invalidateQueries({ queryKey: conversationKeys.list() });
    },
  });
}

/**
 * **What a refused departure re-reads** — the two lists a court is drawn on, marked stale
 * ([#427](https://github.com/Raketa02/Raketa/issues/427)).
 *
 * A refusal that means *this court is not what the row thought it was* — over, history, the
 * moment passed, not yours — is answered on the list in words, and then by reading again, so a
 * court that has genuinely ended goes when the server says it has. The *when* is the door's
 * (`DepartureDoor` waits for the sheet to be dismissed, so the words are read before the row they
 * are about can go); the *what* is declared here, because a cache effect is this file's to declare
 * — one place to change which lists a court touches, beside the success path that touches them.
 *
 * Returns the act rather than performing it, for the same reason: the component decides the
 * moment, and a hook that fired on mount would be a hook deciding it.
 */
export function useReReadCourtLists(): () => void {
  const client = useQueryClient();

  return () => {
    void client.invalidateQueries({ queryKey: conversationKeys.list() });
    void client.invalidateQueries({ queryKey: challengeKeys.list() });
  };
}
