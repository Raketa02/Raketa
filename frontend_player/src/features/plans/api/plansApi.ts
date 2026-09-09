/**
 * The plan read and the three writes — one route per slot, because ADR-0144 has three events.
 *
 * One of the two layers allowed to read generated types, and the only place these paths are
 * written down.
 *
 * ## One list beside `GET /games`, joined by game id
 *
 * The plan is **not** a field on a game and never will be
 * ([ADR-0148](../../../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
 * §8): *a game is a record of an evening and a plan is an agreement about a future, and the two
 * contexts do not read each other.* So the join is the client's, and it is one extra list rather
 * than one read per card.
 *
 * **A game with nothing agreed is absent from the list**, not present with three nulls — *a plan
 * is born by being used* — so *no plan* and *nothing agreed* are one state on the wire as well as
 * in `domain/slots.ts`.
 *
 * **There is no `read_at` on the answer, deliberately.** A plan folds nothing against the clock,
 * so there is no instant for it to have been folded against; the card folds against `GET /games`'
 * own `read_at`, which is what keeps every clock on a surface the same one.
 *
 * ## Three writes and no `Idempotency-Key`
 *
 * **A write of the value already there records nothing and answers `200`** — the server's rule,
 * and it is what stops a room filling with *Tomek set the day* three times over. That is a
 * stronger guarantee than a key would give and it does not expire, so a key beside it would be
 * the weaker of two — `challengesApi`'s own argument about the pair rule.
 *
 * ## A `signal` on the read and none on the writes
 *
 * The asymmetry every feature here draws, arriving for the reason and not a different one: a
 * `GET` records nothing, so an abandoned one costs nobody a row, and each write appends an event
 * to a stream — a cancelled one can leave a slot recorded with nobody holding the answer that
 * says so.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type PlanListResponse = components['schemas']['PlanListResponse'];
type PlanSchema = components['schemas']['PlanSchema'];
type SetPlaceRequest = components['schemas']['SetPlaceRequest'];
type SetDayRequest = components['schemas']['SetDayRequest'];
type SetHourRequest = components['schemas']['SetHourRequest'];

/** The read may be abandoned; a write may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/** **Every plan for the games you are on the court of**, newest arrangement first. */
export function getPlans({ signal }: Cancellable = {}): Promise<PlanListResponse> {
  return httpRequest<PlanListResponse>({
    method: 'GET',
    path: '/api/v1/plans',
    authenticated: true,
    signal,
  });
}

/**
 * *We are meeting here.*
 *
 * `place` crosses as it was tidied: runs of whitespace collapse to one space, empty after that is
 * `the_place_is_empty` and past the cap is `the_place_is_too_long`. **Neither is silently fixed**
 * on either side of the wire.
 */
export function putPlace(gameId: string, body: SetPlaceRequest): Promise<PlanSchema> {
  return httpRequest<PlanSchema>({
    method: 'PUT',
    path: `/api/v1/plans/${gameId}/place`,
    body,
    authenticated: true,
  });
}

/** *We are playing on this day.* A local day in the platform zone, clamped to the horizon. */
export function putDay(gameId: string, body: SetDayRequest): Promise<PlanSchema> {
  return httpRequest<PlanSchema>({
    method: 'PUT',
    path: `/api/v1/plans/${gameId}/day`,
    body,
    authenticated: true,
  });
}

/** *We are playing at this time.* A clock time on the offered grid, validated server-side. */
export function putHour(gameId: string, body: SetHourRequest): Promise<PlanSchema> {
  return httpRequest<PlanSchema>({
    method: 'PUT',
    path: `/api/v1/plans/${gameId}/hour`,
    body,
    authenticated: true,
  });
}
