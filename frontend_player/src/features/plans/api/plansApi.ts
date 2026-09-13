/**
 * The plan read and the four writes — one route per slot, because ADR-0144 has three events, and
 * the lock, because ADR-0155 added a fourth that is an act rather than a slot.
 *
 * One of the two layers allowed to read generated types, and the only place these paths are
 * written down.
 *
 * ## One list beside the rooms and the games, joined by challenge id
 *
 * The plan is **not** a field on a game or on a room and never will be
 * ([ADR-0148](../../../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
 * §8): *a game is a record of an evening and a plan is an agreement about a future, and the two
 * contexts do not read each other.* So the join is the client's, and it is one extra list rather
 * than one read per card — **keyed by `challenge_id`**
 * ([ADR-0164](../../../../../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md)
 * §1), the one id a room and its game both carry, so the room reads its plan by its own id from
 * the moment it opens and a game reads the same plan by the id it was opened from.
 *
 * **One row for every court the reader holds an accepted seat on, written or not** — a court with
 * nothing agreed is a row with three nulls and the anchor, not an absence. Absence means one thing
 * only: no accepted seat on that court — an invitee still deciding gets no row, and neither does
 * somebody who left.
 *
 * **There is no `read_at` on the answer, deliberately.** A plan folds nothing against the clock,
 * so there is no instant for it to have been folded against; the card folds against the surface's
 * own `read_at` — the room's in the chat, the games list's on the game screen — which is what keeps
 * every clock on a surface the same one. The row's `anchor` is not a clock: it is where the day
 * horizon runs from, and it only ever moves later.
 *
 * ## Four writes and no `Idempotency-Key`
 *
 * **A write of the value already there records nothing and answers `200`** — the server's rule,
 * and it is what stops a room filling with *Tomek set the day* three times over. That is a
 * stronger guarantee than a key would give and it does not expire, so a key beside it would be
 * the weaker of two — `challengesApi`'s own argument about the pair rule. **The lock takes the
 * same language and applies it to an act**: locking a plan that is already locked answers `200`
 * and records nothing, and the first lock's moment is the one that stands.
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

/** **One row for every court you may plan, written or not**, newest arrangement first. */
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
export function putPlace(challengeId: string, body: SetPlaceRequest): Promise<PlanSchema> {
  return httpRequest<PlanSchema>({
    method: 'PUT',
    path: `/api/v1/plans/${challengeId}/place`,
    body,
    authenticated: true,
  });
}

/** *We are playing on this day.* A local day in the platform zone, clamped to the horizon. */
export function putDay(challengeId: string, body: SetDayRequest): Promise<PlanSchema> {
  return httpRequest<PlanSchema>({
    method: 'PUT',
    path: `/api/v1/plans/${challengeId}/day`,
    body,
    authenticated: true,
  });
}

/** *We are playing at this time.* A clock time on the offered grid, validated server-side. */
export function putHour(challengeId: string, body: SetHourRequest): Promise<PlanSchema> {
  return httpRequest<PlanSchema>({
    method: 'PUT',
    path: `/api/v1/plans/${challengeId}/hour`,
    body,
    authenticated: true,
  });
}

/**
 * *We are agreed.*
 *
 * **No body**: the value is the three slots and they are already recorded, so sending one back
 * would be the second place that fact is true. A `PUT` for the reason the slot routes are — the
 * same act twice lands the same state. Refused `the_court_is_not_whole` while a seat is open or
 * unanswered — **the lock waits for the court** (ADR-0164 §5), asked first — and
 * `the_plan_is_not_complete` while a slot is empty, each a **409 rather than a silent `200`**,
 * because a no-op there would leave this client believing it had agreed a plan it had not
 * (ADR-0155 §3).
 */
export function putLock(challengeId: string): Promise<PlanSchema> {
  return httpRequest<PlanSchema>({
    method: 'PUT',
    path: `/api/v1/plans/${challengeId}/lock`,
    authenticated: true,
  });
}
