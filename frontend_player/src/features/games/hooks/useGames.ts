/**
 * The read, the two writes, and the lookup that stands in for a route that does not exist.
 *
 * | | |
 * | --- | --- |
 * | `useGames` | `GET /games` — arranged, played and finished in one list |
 * | `useGame` | one game **out of that list**, because there is no `GET /games/{id}` |
 * | `useStateResult` | `POST /result` — the entry, the correction and the counter |
 * | `useAcceptResult` | `POST /result/acceptance` — from across the net, one is enough |
 * | `useReportNoShow` | `POST /no-shows` — *Kuba didn't come*, on a booked game (#560) |
 * | `useDisputeNoShow` | `POST /no-shows/dispute` — *I was there*, the reported player's (#560) |
 *
 * ## Both writes invalidate and neither is optimistic
 *
 * A standing is *derived from the record and the clock*, so the only client that can be right
 * about what a game becomes is one that asks. An optimistic entry would have to fold
 * `AWAITING_ANSWER`, a deadline and a grace on this side — a second implementation of the rule
 * ADR-0137 §2 put in exactly one place — and it would be wrong the first time the clock
 * disagreed. The answer is dropped for the reason the use-cases give, and the list is
 * invalidated: the next read is one fold, over everything, against one `read_at`.
 *
 * ## Neither of them overrides `networkMode`, and the test is the app's own
 *
 * *Does this act carry a deadline the player chose?* The send in `challenges` does — a
 * challenge's answer window is derived **at send**, so a tap deferred to the next reconnect asks
 * four people at a moment nobody picked. Neither of these does. A proposal's day starts whenever
 * the proposal lands and is the same twenty-four hours for the other side however late it is,
 * and an acceptance's grace runs from the **score** rather than from the tap, so a queued one
 * settles exactly the moment it would have. Both therefore **pause** like everything else in the
 * app, and the screen renders `offlineMessage('resumes')` at the control that is waiting.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Game } from '../domain/game';
import { acceptResult } from '../use-cases/acceptResult';
import { disputeNoShow, reportNoShow, type NoShowToReport } from '../use-cases/noShows';
import { readGames } from '../use-cases/readGames';
import { stateResult, type StatedResult } from '../use-cases/stateResult';

import { gameKeys } from './gameKeys';

/**
 * **What a composer re-reads once a write lands** — a booked game's Home and details, which this
 * feature cannot name (#560). Run from the mutation rather than from the press, so a write that
 * waited out a lost connection still re-reads them after the screen that sent it has gone.
 */
export interface AfterAWrite {
  readonly reread?: () => void;
}

export function useGames() {
  return useQuery<readonly Game[], AppError>({
    queryKey: gameKeys.list(),
    queryFn: ({ signal }) => readGames({ signal }),
  });
}

/**
 * One game, found in the list.
 *
 * `undefined` covers three states and the screen tells them apart with `isPending` and `error`
 * from `useGames` beside it: the list has not landed, the read failed, or **no game of yours has
 * that id** — which is the client half of `you_were_not_on_this_court` and the honest answer to
 * a link that has gone stale. The server refuses to separate *it does not exist* from *you did
 * not play in it*, because separating them would answer *is this id real* about four strangers'
 * evening, and this side keeps that refusal rather than undoing it with a 404 of its own.
 */
export function useGame(gameId: string | undefined) {
  const games = useGames();

  return {
    ...games,
    // No id is no game, which is `usePlan`'s shape one feature over: a room whose line-up has not
    // completed asks with nothing and is answered with nothing, rather than with a sentinel.
    game: gameId === undefined ? undefined : games.data?.find((one) => one.gameId === gameId),
  };
}

/** *This is the score* — the entry, the correction and the counter, which are one request. */
export function useStateResult({ reread }: AfterAWrite = {}) {
  const client = useQueryClient();

  return useMutation<void, AppError, StatedResult>({
    mutationFn: stateResult,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: gameKeys.list() });
      reread?.();
    },
  });
}

/** *That is what happened* — and it goes on offering the disagreement until the grace passes. */
export function useAcceptResult({ reread }: AfterAWrite = {}) {
  const client = useQueryClient();

  return useMutation<void, AppError, string>({
    mutationFn: acceptResult,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: gameKeys.list() });
      reread?.();
    },
  });
}

/**
 * ***Kuba didn't come*** — a no-show report (#560). Invalidates and is never optimistic, as the
 * result's writes are: what the game becomes — the report waiting out its day — is the server's
 * fold. It pauses offline like them too: the reported player's day runs from the report landing,
 * so nothing about it is fixed by the moment it is tapped.
 */
export function useReportNoShow({ reread }: AfterAWrite = {}) {
  const client = useQueryClient();

  return useMutation<void, AppError, NoShowToReport>({
    mutationFn: reportNoShow,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: gameKeys.list() });
      reread?.();
    },
  });
}

/**
 * ***I was there*** — the reported player's dispute (#560). The same posture: invalidate, never
 * optimistic, pause offline. **It does carry a deadline** — the report's day — and a dispute queued
 * past it is refused by name (`the_dispute_window_has_closed`) and said so, rather than sent
 * early by a rule this side would have to restate.
 */
export function useDisputeNoShow({ reread }: AfterAWrite = {}) {
  const client = useQueryClient();

  return useMutation<void, AppError, string>({
    mutationFn: disputeNoShow,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: gameKeys.list() });
      reread?.();
    },
  });
}
