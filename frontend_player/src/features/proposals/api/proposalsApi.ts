/**
 * **The group deck's read, a player's answers, their own reads, and a booked game with its seats**
 * — one of the two layers allowed to read generated types, and the only place these paths are
 * written down ([#553](https://github.com/Raketa02/Raketa/issues/553),
 * [#554](https://github.com/Raketa02/Raketa/issues/554), #556, #557; #538–#545).
 *
 * | | |
 * | --- | --- |
 * | `getGroupDeck` | `GET /pools/{id}/deck?sport&kind` — a group's Games tab, the pool filed under the group's id |
 * | `postYes` | `POST /proposals/{id}/yes` — *I'm in*, silent and free |
 * | `postNo` | `POST /proposals/{id}/no` — *Not this time*, silent and final |
 * | `deleteYes` | `DELETE /proposals/{id}/yes` — withdraw a yes before the game fills |
 * | `getLiveYeses` | `GET /players/me/live-yeses` — every yes on a game still filling, across groups |
 * | `getGamesAndMoney` | `GET /players/me/games-and-money` — the two limits, and what the form offers |
 * | `putGamesAndMoney` | `PUT /players/me/games-and-money` — both limits, on every tap |
 * | `getPaymentsToConfirm` | `GET /players/me/payments-to-confirm` — every refused share of the reader's still waiting for them (#555) |
 * | `postPaymentConfirmation` | `POST /seat-charges/{id}/confirmation` — *I confirmed my payment*: the yes again (#555) |
 * | `getHome` | `GET /home` — the reader's booked games, soonest first, and Home's badge (#542, #556) |
 * | `getBooking` | `GET /bookings/{id}` — one booked game in detail, for a player in it or one offered its open seat (#542, #545) |
 * | `postSeat` | `POST /bookings/{id}/seats` — *I'm in* on a rescue: the seat taken, paid at once (#545) |
 * | `postRescueNo` | `POST /bookings/{id}/no` — a no to a *Seat open* card (#545) |
 * | `postDeparture` | `POST /bookings/{id}/departure` — *Leave the game* (#544) |
 * | `getProposal` | `GET /proposals/{id}` — one game still filling in detail, with what the reader may do (#542) |
 * | `getFillIn` | `GET /pools/{id}/fill-in?sport` — a group's *Seats to fill* and the tab's badge (#545) |
 *
 * ## A `signal` on the read and none on the writes
 *
 * `groupsApi`'s asymmetry, for its reason: a `GET` records nothing, and an abandoned one costs
 * nobody a row; an answer appends to the game's stream, and a cancelled one can leave a yes
 * recorded with nobody holding the reply that says so.
 *
 * ## No `Idempotency-Key`, because every answer is already safe to repeat
 *
 * By the routes' own word: *a yes already said records nothing and answers the same*, *a second
 * no records nothing*, and *withdrawing a yes never said records nothing*. None is retried all the
 * same — every mutation's rule — and the card has flown, or the button is busy, while one is in
 * flight.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

/** The read may be abandoned; an answer may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/**
 * A group's deck for one sport and one kind. `pool_not_found` for no such group and for one the
 * reader is not in; `block_state_unavailable` (503) when who fits whom could not be read.
 */
export function getGroupDeck(
  poolId: string,
  sport: Schemas['Sport'],
  kind: Schemas['SearchMode'],
  { signal }: Cancellable = {},
): Promise<Schemas['GroupDeckResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/pools/${encodeURIComponent(poolId)}/deck?sport=${sport}&kind=${kind}`,
    authenticated: true,
    signal,
  });
}

/**
 * *I'm in.* Answers the seats still open with this yes counted — and, when it was the last, what the
 * fill did: `booked`, or `your_payment` when this player's share could not be held (#541).
 * `payment_method_required` before a first yes; `payment_to_confirm` (`details.seat_charge_id`)
 * while a refused payment of theirs waits on this game.
 */
export function postYes(proposalId: string): Promise<Schemas['YesAnswerResponse']> {
  return httpRequest({
    method: 'POST',
    path: `${proposalPath(proposalId)}/yes`,
    authenticated: true,
  });
}

/** *Not this time.* The card never comes back. */
export function postNo(proposalId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${proposalPath(proposalId)}/no`,
    authenticated: true,
  });
}

/** *Withdraw* — the seat is open again, and the player may say yes again while it fills. */
export function deleteYes(proposalId: string): Promise<void> {
  return httpRequest<void>({
    method: 'DELETE',
    path: `${proposalPath(proposalId)}/yes`,
    authenticated: true,
  });
}

/** The reader's live yeses, soonest game first, with the cap per sport. */
export function getLiveYeses({ signal }: Cancellable = {}): Promise<Schemas['LiveYesesResponse']> {
  return httpRequest({
    method: 'GET',
    path: '/api/v1/players/me/live-yeses',
    authenticated: true,
    signal,
  });
}

/** The reader's refused shares still waiting for them, soonest game first. */
export function getPaymentsToConfirm({ signal }: Cancellable = {}): Promise<
  Schemas['PaymentsToConfirmResponse']
> {
  return httpRequest({
    method: 'GET',
    path: '/api/v1/players/me/payments-to-confirm',
    authenticated: true,
    signal,
  });
}

const GAMES_AND_MONEY_PATH = '/api/v1/players/me/games-and-money';

export function getGamesAndMoney({ signal }: Cancellable = {}): Promise<
  Schemas['GamesAndMoneyResponse']
> {
  return httpRequest({ method: 'GET', path: GAMES_AND_MONEY_PATH, authenticated: true, signal });
}

/**
 * Save both limits. `games_per_week_out_of_range` and `most_ill_pay_not_offered` (400) for a value
 * the form does not offer — nothing saved. The same answer twice records nothing, so a tap that
 * lands twice is harmless; it is not retried all the same.
 */
export function putGamesAndMoney(
  body: Schemas['GamesAndMoneyRequest'],
): Promise<Schemas['GamesAndMoneyResponse']> {
  return httpRequest({ method: 'PUT', path: GAMES_AND_MONEY_PATH, authenticated: true, body });
}

/**
 * **The yes again, on a payment the player confirmed in the app** — asked of the provider, never
 * taken on the phone's word, and answered as a yes is. `payment_not_confirmed` while the provider
 * still waits; `proposal_is_full` when somebody else took the seat first. Not retried: it can book
 * a game and charge everybody else.
 */
export function postPaymentConfirmation(
  seatChargeId: string,
): Promise<Schemas['YesAnswerResponse']> {
  return httpRequest({
    method: 'POST',
    path: `/api/v1/seat-charges/${encodeURIComponent(seatChargeId)}/confirmation`,
    authenticated: true,
  });
}

/**
 * **Home** — every game the reader booked, soonest first, the ended ones too (the client shelves
 * them), each with its status and money line folded at `read_at`, and how many need them.
 */
export function getHome({ signal }: Cancellable = {}): Promise<Schemas['HomeResponse']> {
  return httpRequest({ method: 'GET', path: '/api/v1/home', authenticated: true, signal });
}

/**
 * **A booked game in detail**, for a player in it — with the reader's check-in code on the game's
 * day — or for a member its open seat is offered to, who reads it from outside (`rescue`, #545).
 * `booking_not_found` (404) for a booking that does not exist and for one that is neither.
 */
export function getBooking(
  bookingId: string,
  { signal }: Cancellable = {},
): Promise<Schemas['BookingDetailsResponse']> {
  return httpRequest({
    method: 'GET',
    path: bookingPath(bookingId),
    authenticated: true,
    signal,
  });
}

/**
 * **I'm in on a rescue** — the seat that opened first, held and taken on the club's account at once
 * (#545), answered as a yes is: `booked`, or `your_payment` when the share could not be held. The
 * first join wins: `seat_just_taken` for the second. Not retried: it charges.
 */
export function postSeat(bookingId: string): Promise<Schemas['YesAnswerResponse']> {
  return httpRequest({
    method: 'POST',
    path: `${bookingPath(bookingId)}/seats`,
    authenticated: true,
  });
}

/** *Not this time* on a *Seat open* card — the card does not come back; the row stays (#545). */
export function postRescueNo(bookingId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${bookingPath(bookingId)}/no`,
    authenticated: true,
  });
}

/**
 * **Leave the game** (#544) — refunded at once less the card fee before the club's cut-off, only
 * when somebody takes the seat after it, and the yes and the request withdrawn while an On request
 * club decides. `game_has_started` and `booking_is_called_off` (409) where there is nothing to
 * leave. Not retried: it moves money.
 */
export function postDeparture(bookingId: string): Promise<Schemas['DepartureResponse']> {
  return httpRequest({
    method: 'POST',
    path: `${bookingPath(bookingId)}/departure`,
    authenticated: true,
  });
}

/**
 * **A game still filling, in detail** (#542) — for anybody dealt it: who is In, the sides and their
 * forecast, the club and its distance, the share and the book-by, the overlap, and what the reader
 * may do now. `proposal_not_found` (404) for a game they were never dealt.
 */
export function getProposal(
  proposalId: string,
  { signal }: Cancellable = {},
): Promise<Schemas['ProposalDetailsResponse']> {
  return httpRequest({
    method: 'GET',
    path: proposalPath(proposalId),
    authenticated: true,
    signal,
  });
}

/**
 * **A group's Fill in tab** for one sport (#545) — *Seats to fill*, soonest first, and the tab's
 * badge. *You're In* is the live yeses. `pool_not_found` for no such group and one the reader is not
 * in; `block_state_unavailable` (503) when who fits whom could not be read.
 */
export function getFillIn(
  poolId: string,
  sport: Schemas['Sport'],
  { signal }: Cancellable = {},
): Promise<Schemas['FillInResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/pools/${encodeURIComponent(poolId)}/fill-in?sport=${sport}`,
    authenticated: true,
    signal,
  });
}

function bookingPath(bookingId: string): string {
  return `/api/v1/bookings/${encodeURIComponent(bookingId)}`;
}

function proposalPath(proposalId: string): string {
  return `/api/v1/proposals/${encodeURIComponent(proposalId)}`;
}
