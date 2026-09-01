/**
 * The deck's wire: one deal, and the two answers to a card.
 *
 * One of the two layers allowed to read generated types, and the only place these four paths
 * are written down.
 *
 * ## `POST /deck` is not idempotent either, and carries no key for the same reason
 *
 * *"A spent deal deals again"* — posting again is a **new deal with a new `search_id`**, so an
 * `Idempotency-Key` here would be a claim the route makes the opposite of, exactly as it would
 * on `POST /searches`. What protects a player from a double tap is the control being busy, and
 * what protects them from a retry storm is that nothing in Play retries without them asking.
 *
 * **No `signal`.** A deal records server-side before it answers, so a cancelled request leaves
 * a deal minted and nobody holding its id — the state `search_not_found` describes, and the
 * one this screen must not manufacture (`api/playSearchApi.ts`, `domain/retryTarget`).
 *
 * ## The two answers, and why they are Play's
 *
 * A deck yes is `POST /interest`, a **matchmaking** write: the challenge a mutual opens is
 * minted server-side and inline through a port, so nothing here reaches another person
 * directly. Left unstated the deck lands in `challenges/` because *Let's play* sounds like a
 * send ([`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md)
 * §8). That is also why the pause is kept here: `features/challenges/` alone sets
 * `networkMode: 'always'`, and these two are not sends.
 *
 * **Both carry `search_id` and neither carries a position.** The origin key is required —
 * *"a yes with no origin is refused rather than recorded with a null link"* — and the backend
 * reads the position off the cited search's own rows, so the link is true by construction
 * rather than by a client being honest about where it was scrolled to.
 *
 * **`POST /passes` answers `204` and no route anywhere returns a pass** — not to the passer,
 * not as a count, not as *"you have passed on twelve people"*. There is nothing here to type
 * as a response because there is nothing to read.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type DealDeckRequest = components['schemas']['DealDeckRequest'];
type ShortlistResponse = components['schemas']['ShortlistResponse'];
type ExpressInterestRequest = components['schemas']['ExpressInterestRequest'];
type ExpressedInterestResponse = components['schemas']['ExpressedInterestResponse'];
type RecordPassRequest = components['schemas']['RecordPassRequest'];
type InterestListResponse = components['schemas']['InterestListResponse'];

/**
 * Deal one batch: at most ten cards, one `search_id`, and the pool they came from.
 *
 * **An empty deal is a `200`.** The honest empty state is an answer rather than a failure, and
 * the pool beside it is described either way — which is what lets the screen tell *you have
 * seen everybody* from *nobody is in range* without a second request.
 */
export function dealDeck(body: DealDeckRequest): Promise<ShortlistResponse> {
  return httpRequest<ShortlistResponse>({
    method: 'POST',
    path: '/api/v1/deck',
    body,
    authenticated: true,
  });
}

/**
 * *Let's play* — one tap, and the one thing it tells you about the other person.
 *
 * `mutual` is `true` when they had already said it to you, and it is earned: a one-sided yes
 * is told to nobody, in either direction. `201` and `200` are the same shape — the second is
 * *you had already said this* — so nothing here branches on the status.
 */
export function expressInterest(body: ExpressInterestRequest): Promise<ExpressedInterestResponse> {
  return httpRequest<ExpressedInterestResponse>({
    method: 'POST',
    path: '/api/v1/interest',
    body,
    authenticated: true,
  });
}

/** *Not today* — recorded, and returned by nothing, ever. */
export function recordPass(body: RecordPassRequest): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: '/api/v1/passes',
    body,
    authenticated: true,
  });
}

/**
 * Your own *Let's play* yeses: outgoing, mutual, and where each sport stands against its cap.
 *
 * **There is no incoming list and there will not be one** — a yes nobody has answered stays
 * silent in both directions, which is what makes saying yes low-stakes
 * ([ADR-0109](../../../../../docs/adr/0109-a-read-back-names-what-it-withholds.md)). So the
 * deck's own count is a count of *yours*, and the segment above it says so.
 */
export function readInterest({ signal }: ReadInterestOptions = {}): Promise<InterestListResponse> {
  return httpRequest<InterestListResponse>({
    method: 'GET',
    path: '/api/v1/interest',
    authenticated: true,
    signal,
  });
}

/**
 * The **read** takes a `signal` where the three writes above take none, and the asymmetry is
 * the whole of `deckApi`'s cancellation rule.
 *
 * A `GET` records nothing, so a cancelled one leaves no trace and costs nobody a row — which
 * is why Part 7's *"pass Query's `signal` through to `fetch`"* applies to it unreservedly. A
 * deal, a yes and a pass all **record server-side before they answer**, so a cancelled one
 * leaves a record nobody holds: the state `origin_search_not_found` describes, and the one
 * this screen must not manufacture.
 */
export interface ReadInterestOptions {
  readonly signal?: AbortSignal;
}
