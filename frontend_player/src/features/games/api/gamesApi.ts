/**
 * The three routes the result argument is — read the games, state a score, agree with one — and the
 * four that say who turned up at a booked game's court (#658).
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
 * `the_result_is_settled`, because the first settled the result at once (#654). The rule is the
 * mechanism, and a key beside it would be the weaker of two — the same argument `challengesApi`
 * makes about the pair rule.
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

type ArrivalRequest = components['schemas']['ArrivalRequest'];
type GameListResponse = components['schemas']['GameListResponse'];
type GameSchema = components['schemas']['GameSchema'];
type NotHereYetRequest = components['schemas']['NotHereYetRequest'];
type PresenceConfirmationRequest = components['schemas']['PresenceConfirmationRequest'];
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
 * It settles the result at once and closes the game (#654): the response is the game
 * `CONFIRMED`, and no different score is taken after it.
 */
export function postResultAcceptance(gameId: string): Promise<GameSchema> {
  return httpRequest<GameSchema>({
    method: 'POST',
    path: `/api/v1/games/${gameId}/result/acceptance`,
    authenticated: true,
  });
}

/**
 * ***Oscar isn't here yet*** — on a booked game, in its first half hour, about somebody else on the
 * court (#658; the backend's #657). **Made at the club**: the body carries the fix the phone read at
 * the tap, which the backend measures against the club's point and drops. Saying it of somebody
 * already awaited answers the same and writes nothing, which is why it needs no key.
 */
export function postNotHereYet(gameId: string, body: NotHereYetRequest): Promise<GameSchema> {
  return httpRequest<GameSchema>({
    method: 'POST',
    path: `/api/v1/games/${gameId}/attendance/not-here-yet`,
    body,
    authenticated: true,
  });
}

/**
 * ***I'm here*** with your own id, ***they're here*** with somebody else's — from the club, in the
 * first half hour. **The first arrival is the one that counts**; a second is refused by name
 * (`already_arrived`).
 */
export function postArrival(gameId: string, body: ArrivalRequest): Promise<GameSchema> {
  return httpRequest<GameSchema>({
    method: 'POST',
    path: `/api/v1/games/${gameId}/attendance/arrival`,
    body,
    authenticated: true,
  });
}

/**
 * ***I was there*** — you Didn't come and your phone died at the court. Within a day of the half
 * hour's end, from wherever you are: no position is asked, because somebody else on the court
 * confirming it is the proof. A second claim writes nothing.
 */
export function postPresenceClaim(gameId: string): Promise<GameSchema> {
  return httpRequest<GameSchema>({
    method: 'POST',
    path: `/api/v1/games/${gameId}/attendance/claim`,
    authenticated: true,
  });
}

/**
 * ***Yes, they were here*** — about somebody else's *I was there*, inside the same day. It turns
 * Didn't come into Came late. A second confirmation writes nothing.
 */
export function postPresenceConfirmation(
  gameId: string,
  body: PresenceConfirmationRequest,
): Promise<GameSchema> {
  return httpRequest<GameSchema>({
    method: 'POST',
    path: `/api/v1/games/${gameId}/attendance/confirmation`,
    body,
    authenticated: true,
  });
}
