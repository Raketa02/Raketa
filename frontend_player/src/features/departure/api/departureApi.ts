/**
 * The wire adapter for the departure route. One path, two methods.
 *
 * `GET` states what leaving is worth; `POST` takes it. **Both answer with the same
 * screen**, because a refusal is not a second shape (`ADR-0070`): a quote that has
 * fallen, a match that has started, a second tap by somebody who has already left
 * — all of them come back as what a success returns, which is what is true now.
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

type DepartureScreenResponse = components['schemas']['DepartureScreenResponse'];
type DepartureWriteResponse = components['schemas']['DepartureWriteResponse'];
type DepartRequest = components['schemas']['DepartRequest'];

/**
 * Fails to compile if the write stops being *a label and a key*.
 *
 * The quote crosses as a `string` here rather than as the four-member union,
 * because what this sends is the label the screen was showing — carried back
 * unread, exactly as it arrived — and the union would oblige this layer to narrow
 * a value it is deliberately not reading. The pin is what keeps that honest: a
 * renamed field, a quote that stops being a label, or a key that stops being a
 * string all fail `pnpm typecheck` here rather than reaching the server as a body
 * it rejects.
 *
 * A label this build cannot name never gets this far — the button that would send
 * it is not drawn, because a control whose consequence the app cannot state is the
 * one outcome worse than silence.
 */
export type RequestIsALabelAndAKey = AssertTrue<
  DepartRequest extends { quote: string; idempotency_key: string } ? true : false
>;

function departurePath(matchId: string): string {
  return `/api/v1/matches/${encodeURIComponent(matchId)}/departure`;
}

export interface ReadDepartureOptions {
  readonly matchId: string;
  readonly signal?: AbortSignal;
}

/** What leaving is worth right now, and what it could still become. */
export function readDeparture({
  matchId,
  signal,
}: ReadDepartureOptions): Promise<DepartureScreenResponse> {
  return httpRequest<DepartureScreenResponse>({
    method: 'GET',
    path: departurePath(matchId),
    authenticated: true,
    signal,
  });
}

export interface LeaveMatchOptions {
  readonly matchId: string;
  /**
   * The label she was looking at, sent back unread.
   *
   * A label and never an amount (`ADR-0033`): an amount moves for reasons that
   * have nothing to do with leaving — a discount landing, a club price change —
   * and refusing on those is noise.
   */
  readonly quote: string;
  readonly idempotencyKey: string;
  readonly signal?: AbortSignal;
}

/** Leave at the quoted outcome. Answers this screen **and** Now's update. */
export function leaveMatch({
  matchId,
  quote,
  idempotencyKey,
  signal,
}: LeaveMatchOptions): Promise<DepartureWriteResponse> {
  return httpRequest<DepartureWriteResponse>({
    method: 'POST',
    path: departurePath(matchId),
    body: { quote, idempotency_key: idempotencyKey },
    authenticated: true,
    signal,
  });
}
