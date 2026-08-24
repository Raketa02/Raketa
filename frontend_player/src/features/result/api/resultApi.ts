/**
 * The wire adapter for the result route. Two paths, three calls.
 *
 * `GET .../result` states what the conversation is doing; `POST .../result` puts a
 * score on the table; `POST .../result/acceptance` agrees with the one that is
 * there. **All three answer with the same screen**, because a refusal is not a
 * second shape (`ADR-0070`): a side that has already spoken, a result that settled
 * while her screen was open, a stale accept — every one comes back as what a
 * success returns, which is what is true now.
 *
 * **Two writes and not three.** Entering, correcting and countering are one act at
 * three moments, and which one a given score is depends on what is already on the
 * table — so a client picking between two endpoints would be holding exactly
 * `ADR-0048`'s cap, which is the one thing `ADR-0053` leaves the phone none of. The
 * score goes to one address and the server decides what it was. Accepting has its
 * own address because it **carries nothing**, and one endpoint whose meaning turned
 * on whether a field was present is the *not there / there and empty* confusion the
 * result block is itself shaped to avoid.
 *
 * **The path says `matches` and there is no `GET /matches/{id}` beside it.** The
 * backend refused a general match resource on purpose, so nothing here may grow
 * one: a second call to a sibling path would be this screen authoring the
 * match-detail contract from the outside.
 *
 * Nothing here decides anything. Which match belongs to the route, when to ask
 * belongs to the hooks, and what the answer means belongs above.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

import type { AssertTrue } from '../mappers/codes';

type ResultScreenResponse = components['schemas']['ResultScreenResponse'];
type ResultWriteResponse = components['schemas']['ResultWriteResponse'];
type ProposeScoreRequest = components['schemas']['ProposeScoreRequest'];

/**
 * Fails to compile if the write stops being *a list of pairs*.
 *
 * `ProposeScoreRequest.sets` is the whole body, and the shape is the one thing this
 * layer genuinely depends on — a renamed field, a score that stops being pairs of
 * integers, or a body that grows a second required field would otherwise reach the
 * server as something it rejects, at runtime, on the one screen where a rejected
 * body loses what she typed.
 *
 * What it deliberately does **not** pin is a bound on either number. The wire's own
 * bound is a door and the rule is the server's permissive validator, which knows
 * the sport — and this app holds no second opinion about what a real score is.
 */
export type RequestIsPairsOfNumbers = AssertTrue<
  ProposeScoreRequest extends { sets: (readonly [number, number])[] } ? true : false
>;

function resultPath(matchId: string): string {
  return `/api/v1/matches/${encodeURIComponent(matchId)}/result`;
}

export interface ReadResultOptions {
  readonly matchId: string;
  readonly signal?: AbortSignal;
}

/** What this match's result conversation is doing, and what she may do about it. */
export function readResult({ matchId, signal }: ReadResultOptions): Promise<ResultScreenResponse> {
  return httpRequest<ResultScreenResponse>({
    method: 'GET',
    path: resultPath(matchId),
    authenticated: true,
    signal,
  });
}

export interface ProposeScoreOptions {
  readonly matchId: string;
  /**
   * The sets she typed, **her side first**.
   *
   * The same order the screen showed her, which the server put her side first in on
   * the way out — so the order coming back is the one thing that cannot be misread.
   * Which player each integer belongs to is the seats' business and hers is not on
   * the wire at all.
   */
  readonly sets: readonly (readonly [number, number])[];
  readonly signal?: AbortSignal;
}

/** Enter a score, correct her own side's, or counter the other side's. */
export function proposeScore({
  matchId,
  sets,
  signal,
}: ProposeScoreOptions): Promise<ResultWriteResponse> {
  return httpRequest<ResultWriteResponse>({
    method: 'POST',
    path: resultPath(matchId),
    body: { sets },
    authenticated: true,
    signal,
  });
}

export interface AcceptResultOptions {
  readonly matchId: string;
  readonly signal?: AbortSignal;
}

/** Agree, from the opposing side, with what is on the table. Carries nothing. */
export function acceptResult({
  matchId,
  signal,
}: AcceptResultOptions): Promise<ResultWriteResponse> {
  return httpRequest<ResultWriteResponse>({
    method: 'POST',
    path: `${resultPath(matchId)}/acceptance`,
    authenticated: true,
    signal,
  });
}
