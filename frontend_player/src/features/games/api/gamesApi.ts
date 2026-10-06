/**
 * The three routes the result argument is — read the games, state a score, agree with one — and
 * the one act on a game that is not about a result: clearing a called-off game's card.
 *
 * One of the two layers allowed to read generated types, and the only place these paths are
 * written down.
 *
 * ## One route for three acts, and none of them is named here
 *
 * `POST /games/{id}/result` is the entry, the correction **and** the counter — *"one request
 * for three acts, and the record decides which"*. Naming the act on the request would be a
 * client that could name it wrongly, and a mislabelled correction is a proposal nobody may
 * make. What the client decides is what to **draw**, and that is `domain/resultArgument.ts`.
 *
 * ## No `Idempotency-Key`, and none of these is a repeat that would go through twice
 *
 * The only mutation in this app that carries one is the profile commit, whose key is minted
 * with the draft. Nothing here needs one: a second identical `POST /result` from the proposing
 * side is a **correction to the same score**, which is free and changes nothing but the day the
 * other side has to answer in, and a second acceptance is refused by name with
 * `the_result_is_already_accepted`. The rule is the mechanism, and a key beside it would be the
 * weaker of two — the same argument `challengesApi` makes about the pair rule.
 *
 * ## A `signal` on the read and none on the writes
 *
 * The asymmetry `playSearchApi` and `challengesApi` both draw, arriving for the reason and not
 * a different one: a `GET` records nothing, so an abandoned one costs nobody a row, and both
 * writes append an event to a stream — a cancelled one can leave a score on the table with
 * nobody holding the answer that says so.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type GameListResponse = components['schemas']['GameListResponse'];
type GameSchema = components['schemas']['GameSchema'];
type ReportANoShowRequest = components['schemas']['ReportANoShowRequest'];
type StateResultRequest = components['schemas']['StateResultRequest'];

/** The read may be abandoned; a write may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/**
 * Every game you were on the court of, newest arrangement first — **arranged, played and
 * finished in one list.**
 *
 * The standings on it are folded against `read_at`, which travels with them so a client's
 * countdowns and the standings beside them cannot come from two readings of the clock.
 */
export function getGames({ signal }: Cancellable = {}): Promise<GameListResponse> {
  return httpRequest<GameListResponse>({
    method: 'GET',
    path: '/api/v1/games',
    authenticated: true,
    signal,
  });
}

/** *This is the score.* The answer is the game as it stands with your score on the table. */
export function postResult(gameId: string, body: StateResultRequest): Promise<GameSchema> {
  return httpRequest<GameSchema>({
    method: 'POST',
    path: `/api/v1/games/${gameId}/result`,
    body,
    authenticated: true,
  });
}

/**
 * *That is what happened.* **From across the net, and one opponent is enough.**
 *
 * It does not settle the result immediately: the grace runs from the score rather than from
 * this tap, so inside it a disagreement still wins.
 */
export function postResultAcceptance(gameId: string): Promise<GameSchema> {
  return httpRequest<GameSchema>({
    method: 'POST',
    path: `/api/v1/games/${gameId}/result/acceptance`,
    authenticated: true,
  });
}

/**
 * ***Kuba didn't come*** — on a booked game whose hour has come, by somebody who came, about
 * somebody else on the court (#560; the backend's #547). The game does not count from here on, and
 * the reported player has a day to dispute it. A second report of the same player answers the same
 * and writes nothing, which is why it needs no key.
 */
export function postNoShow(gameId: string, body: ReportANoShowRequest): Promise<GameSchema> {
  return httpRequest<GameSchema>({
    method: 'POST',
    path: `/api/v1/games/${gameId}/no-shows`,
    body,
    authenticated: true,
  });
}

/**
 * ***I was there*** — the reported player, inside their day (#560). The report falls and nothing
 * goes on their record; the game still does not count. A second dispute writes nothing.
 */
export function postNoShowDispute(gameId: string): Promise<GameSchema> {
  return httpRequest<GameSchema>({
    method: 'POST',
    path: `/api/v1/games/${gameId}/no-shows/dispute`,
    authenticated: true,
  });
}
