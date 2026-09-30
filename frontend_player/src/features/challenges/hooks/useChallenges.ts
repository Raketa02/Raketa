/**
 * The send, and the three readings of the one list this feature reads.
 *
 * | | |
 * | --- | --- |
 * | `useSendChallenge` | `POST /challenges` — **pending, never optimistic**, and the one act in the app that fails offline rather than pausing |
 * | `useChallengeInbox` | `GET /challenges` — the Chats tab's `CHALLENGES` section, filtered and ordered |
 * | `useChallengesWaiting` | the same list, counted — the one number on the tab bar |
 * | `useOpenPair` | the same list again, asked **only after** `open_challenge_stands`, to name the pair the refusal would not |
 *
 * ## Three readers, one key, one request
 *
 * The shell mounts the count and the Chats screen mounts the section, and TanStack dedupes both
 * mounts to one fetch of `challengeKeys.list()`. **The badge reads no cache-only entry**: that
 * would leave it blank on a cold start until the player visited Chats, making a count a reward
 * for having already looked ([#326](https://github.com/Raketa02/Raketa/issues/326) §7).
 *
 * `staleTime: 0` is the one override, and it is the same one this file already made for the
 * pair's name. The badge is chrome that is continuously on screen, so thirty seconds of
 * staleness is a number lying about what the player owes; and the app's own focus refetch —
 * already wired from `AppState` — **is** the once-a-day player's case, which is what makes the
 * count current when they open the app rather than current from the last time they did.
 *
 * **Zeroing is by invalidation, never optimistic.** An optimistic decrement would have to be
 * rolled back on the failure this map classifies as *paused, not failed*, and a badge that
 * ticks down and back up is a worse lie than one that lags by a request.
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
import { useOnReturn } from '@/shared/lib/platform';

import { useCurrentUser } from '@/features/auth/types';

import {
  holdsTheExit,
  leavingWouldEnd,
  pairAlreadyPlaying,
  standingFactsFor,
  type Challenge,
  type LeavingEnds,
} from '../domain/challenge';
import { challengeInbox, challengesWaiting } from '../domain/challengeInbox';
import { courtWith } from '../domain/courtWith';
import type { StandingFacts } from '../domain/standing';
import { readChallenges } from '../use-cases/readChallenges';
import { sendChallenge, type SendAsk, type SentChallenge } from '../use-cases/sendChallenge';

import { challengeKeys } from './challengeKeys';
import { CHALLENGE_MUTATION_OPTIONS } from './challengeMutationOptions';

/**
 * ⚡ becomes a challenge.
 *
 * `CHALLENGE_MUTATION_OPTIONS` is spread whole rather than partly: it is one decision about every
 * act in this feature, and a call site that copied half of it would leave the paused queue
 * reachable, which is the thing the override exists to close.
 *
 * No `retry`. The app-wide mutation default is already `retry: false`, and a send is the one
 * request in this app where an automatic repeat would ask four people twice — refused by the
 * pair rule the second time, which is correct and is still a round trip nobody pressed for.
 */
export function useSendChallenge() {
  const client = useQueryClient();

  return useMutation<SentChallenge, AppError, SendAsk>({
    mutationFn: sendChallenge,
    ...CHALLENGE_MUTATION_OPTIONS,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: challengeKeys.list() });
    },
  });
}

/**
 * **Who on this court you already have a game with** — `undefined` until there is an answer, and
 * `undefined` again when the game in the way is not one of yours.
 *
 * `enabled` is the refusal, and it is the whole reason this reading is switched off by default
 * where the other two are always on — see {@link useChallengeList}.
 *
 * **It answers a player id and never a name.** Turning one into words needs the handle, which is
 * the *court's* to read off the search it was built from — this feature has never seen a
 * name and must not learn to guess one.
 *
 * `undefined` while the answer is on its way, and `undefined` again when there is nobody in it
 * to name. The two are deliberately not told apart: the sentence the screen writes without a
 * name is true in both, and a third state would be a spinner over a refusal that has already
 * been stated.
 */
export function useOpenPair(invitees: readonly string[], enabled: boolean): string | undefined {
  const { data } = useChallengeList(enabled);

  return data === undefined ? undefined : pairAlreadyPlaying(data, invitees);
}

/**
 * **Your challenges, right now** — the one read, at the one posture its three readers share.
 *
 * `enabled` is `useOpenPair`'s refusal, and it is the whole reason that reading is a query with
 * a switch rather than a read the builder makes on arrival: a court is built, looked at and
 * sent from without anybody needing to know what else the organiser has open, and asking on
 * every visit would be a request per builder session to answer a question almost none of them
 * ask. The other two readers are always on.
 *
 * The invitees are **not** in the key. This is one list either way, and keying it per court
 * would mint an entry per line-up for one answer — the derivations over it are free.
 *
 * **Never served from stale cache**, which is the one thing none of the three can afford. The
 * app-wide default is thirty seconds and it is right for almost everything, but: the pair's
 * name is read *after a refusal*, and the second refusal of a session would land inside that
 * window and name whoever the first one named — the wrong person, in the one sentence in the
 * feature that says somebody's handle out loud. And the badge is a count on permanent chrome,
 * where thirty seconds of staleness is the number saying something is waiting when it is not.
 *
 * Zero rather than an invalidation at each call site, because the two are the same instruction
 * and only one of them is stated where the read is.
 */
function useChallengeList(enabled = true, staleTime = 0) {
  return useQuery<readonly Challenge[], AppError>({
    queryKey: challengeKeys.list(),
    queryFn: ({ signal }) => readChallenges({ signal }),
    enabled,
    staleTime,
  });
}

/**
 * The Chats tab's `CHALLENGES` section — the query, with its rows already filtered and ordered.
 *
 * The order is the domain's and is applied here rather than in the section, so the badge above
 * and the list below are two readings of one rule rather than two rules that agree today.
 *
 * `rows` is empty until there is both a list and a reader. Who the reader is comes from
 * `useCurrentUser`, exactly as the Home tab's games list picks its own seat out of a court:
 * no route serves a player their own id, and every rule here is about *your* seat.
 *
 * **Coming back to the section re-reads it** ([#429](https://github.com/Raketa02/Raketa/issues/429)
 * A5, A6). `staleTime: 0` says the list is never *served* stale, and it is not — on a mount, on
 * a foreground. But the section stays **mounted** under the room and the challenge screen the
 * tab pushes over it, and an answer that lands while the player is in the room reaches the
 * room as a line and the list not at all: the nudge re-reads what the room draws and, by
 * design, never this list (`useLiveConversation`). *Back* is neither a mount nor a foreground,
 * so the row read *Waiting on 2 answers* under a room that had just said one of them was in.
 * The return is the moment somebody is looking at the row again, so the return is what marks
 * the list stale — one request, and only then, where re-reading on every nudge would be one
 * per inbound message for a row nobody is looking at.
 */
export function useChallengeInbox() {
  const challenges = useChallengeList();
  const playerId = useCurrentUser().data?.id;
  const client = useQueryClient();

  useOnReturn(() => {
    void client.invalidateQueries({ queryKey: challengeKeys.list() });
  });

  return {
    ...challenges,
    playerId,
    rows:
      challenges.data === undefined || playerId === undefined
        ? []
        : challengeInbox(challenges.data, playerId),
  };
}

/**
 * **Whether this reader may call a game off** — the organiser fact, joined off the list
 * ([#419](https://github.com/Raketa02/Raketa/issues/419),
 * [ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)).
 *
 * A game carries no organiser; the challenge behind it does, and `game.challengeId` is the join
 * key — the shape ADR-0149 §3 chose for exactly this kind of fact, rather than a field on
 * `GET /games` restating a challenge's. It is read off the **list** and not the detail, because
 * the tab bar already holds the list for its badge and every row of it carries what
 * `holdsTheExit` reads — `organiserId`, and each seat's answer — so what a game screen costs is
 * one more observer on a query the app already keeps (refetched on mount at the list's own
 * `staleTime: 0`), rather than a detail read of its own, with its pairing, for one boolean.
 *
 * **Asked only while the composer's own rule holds** — `enabled` is *a seat is open* — on
 * `useOpenPair`'s switch: the control is mounted on every plan-lead screen, and a question about
 * the exit on a full court would refetch the list at `staleTime: 0` for an answer nothing draws.
 *
 * **Fails soft**: switched off, no list yet, no reader yet, no row for this court, or a reader the
 * row does not seat all answer *no* — and *no* draws no control, never a control the act would
 * refuse. Who the reader is comes from `useCurrentUser`, as every other reading of this list
 * takes it.
 */
export function useHoldsTheExit(challengeId: string, enabled: boolean): boolean {
  const { data } = useChallengeList(enabled);
  const playerId = useCurrentUser().data?.id;
  const row = data?.find((one) => one.challengeId === challengeId);

  return enabled && row !== undefined && playerId !== undefined && holdsTheExit(row, playerId);
}

/**
 * **One row, as the list holds it** — for a surface that needs a fact only the list carries:
 * `ended_by` and `game_id`, which the detail read does not serve (ADR-0172 §3–§4), read by the
 * challenge screen for the ended court and by the departure's two doors for their sheet.
 *
 * `useHoldsTheExit`'s shape, the row rather than one answer off it — and `useHeldChallenge`'s
 * posture on the entry: **read what is held, and fetch only if nothing is.** The list is the
 * tab bar's read, kept fresh by that observer at its own `staleTime: 0` whenever the reader is
 * in the app, so a second observer at nought would send a request for a row the cache already
 * holds every time a game screen or a challenge screen mounted (`useHoldsTheExit` gates itself
 * for that reason). A cold route finds nothing held and fetches, and the surface re-folds when
 * it lands. `undefined` is a row the list does not hold, or has not landed.
 */
export function useChallengeRow(challengeId: string): Challenge | undefined {
  const { data } = useChallengeList(true, Infinity);

  return data?.find((one) => one.challengeId === challengeId);
}

/**
 * **What the reader's leaving would do to this court** — `leavingWouldEnd` read off the row the
 * list holds, for the three sheets the departure has ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §9): the Chats row's door, the challenge screen's door and the game screen's control read one
 * hook, so they cannot say different things about one court. Who the reader is comes from
 * `useCurrentUser`, as every other reading of this list takes it; nothing held or nobody yet is
 * today's line.
 */
export function useLeavingWouldEnd(challengeId: string): LeavingEnds | undefined {
  const row = useChallengeRow(challengeId);
  const me = useCurrentUser().data?.id;

  return row === undefined || me === undefined ? undefined : leavingWouldEnd(row, me);
}

/**
 * **Unanswered challenges addressed to you** — the Chats column's number, or nothing at all.
 *
 * `undefined` covers zero, in flight and refused, and the three are deliberately not told
 * apart: they draw the identical absence, because a spinner or a `?` on permanent chrome is
 * anxiety with no act behind it. Zero is folded in with them here rather than at the bar, so
 * the bar takes *a count to draw* rather than a number it has to decide about.
 *
 * It counts nothing until the reader is known, which is the same rule as the section's: every
 * clause of the predicate is about *your* seat.
 *
 * **`active` is whether the bar draws Chats at all** — Classic play
 * ([#550](https://github.com/Raketa02/Raketa/issues/550)). Off, the list is not read for a count
 * nobody would see; the inbox's own section still reads it wherever it is mounted.
 */
export function useChallengesWaiting(active: boolean): number | undefined {
  const { data } = useChallengeList(active);
  const me = useCurrentUser().data?.id;

  if (data === undefined || me === undefined) return undefined;

  const waiting = challengesWaiting(data, me);
  return waiting === 0 ? undefined : waiting;
}

/**
 * **The court the reader shares with one person, as its row would say it** — `courtWith` read
 * off the list the tab bar holds, for the radar's record sheet
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §4). The id, so the surface can find the court's chat; and the standing as it reads to this
 * reader, so the surface can say the court's own line through `standingLine` — the words stay
 * this feature's, and the surface composes them. Nothing about the seats crosses.
 *
 * `useChallengeRow`'s posture on the entry — read what is held, fetch only if nothing is: the
 * sheet is open for a moment, and the list is already fresh whenever the reader is in the app.
 *
 * `undefined` is no court, no list yet, no reader yet, or a court whose standing this build has
 * no words for — which it may not name, and so does not.
 */
export interface CourtWith {
  readonly challengeId: string;
  readonly facts: StandingFacts;
}

export function useCourtWith(playerId: string): CourtWith | undefined {
  const { data } = useChallengeList(true, Infinity);
  const me = useCurrentUser().data?.id;

  if (data === undefined || me === undefined) return undefined;
  const court = courtWith(data, me, playerId);
  if (court === undefined) return undefined;
  const facts = standingFactsFor(court, me);
  return facts === undefined ? undefined : { challengeId: court.challengeId, facts };
}
