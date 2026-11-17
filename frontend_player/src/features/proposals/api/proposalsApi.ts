/**
 * **The group deck's read, a player's answers, their own reads, and a booked game with its seats**
 * — one of the two layers allowed to read generated types, and the only place these paths are
 * written down ([#553](https://github.com/Raketa02/Raketa/issues/553),
 * [#554](https://github.com/Raketa02/Raketa/issues/554), #556, #557; #538–#545).
 *
 * | | |
 * | --- | --- |
 * | `getGroupDeck` | `GET /pools/{id}/deck?sport&kind` — a group's Games tab, the pool filed under the group's id |
 * | `postDeal` | `POST /pools/{id}/deal` — deal the group now, after an intent answer on Games (#741) |
 * | `postYes` | `POST /proposals/{id}/yes` — *I'm in*, silent and free |
 * | `postNo` | `POST /proposals/{id}/no` — *Not this time*, silent and final |
 * | `deleteYes` | `DELETE /proposals/{id}/yes` — withdraw a yes before the game fills |
 * | `getLiveYeses` | `GET /players/me/live-yeses` — every yes on a game still filling, across groups |
 * | `getGamesAndMoney` | `GET /players/me/games-and-money` — the two limits, and what the form offers |
 * | `putGamesAndMoney` | `PUT /players/me/games-and-money` — both limits, on every tap |
 * | `getPaymentsToConfirm` | `GET /players/me/payments-to-confirm` — every refused share of the reader's still waiting for them (#555) |
 * | `postPaymentConfirmation` | `POST /seat-charges/{id}/confirmation` — *I confirmed my payment*: the yes again (#555) |
 * | `getHome` | `GET /home` — the reader's booked games, soonest first, and Home's badge (#542, #556) |
 * | `postNeedsYourAnswerVisit` | `POST /players/me/needs-your-answer/visit` — Needs your answer went for good, naming the watermark of the read it showed (#815, #819) |
 * | `getBooking` | `GET /bookings/{id}` — one booked game in detail, for a player in it or one offered its open seat (#542, #545) |
 * | `postSeat` | `POST /bookings/{id}/seats` — *I'm in* on a rescue: the seat taken, paid at once (#545) |
 * | `postRescueNo` | `POST /bookings/{id}/no` — a no to a *Seat open* card (#545) |
 * | `postDeparture` | `POST /bookings/{id}/departure` — *Leave the game* (#544) |
 * | `getProposal` | `GET /proposals/{id}` — one game still filling in detail, with what the reader may do (#542) |
 * | `getFillIn` | `GET /pools/{id}/fill-in?sport` — a group's *Seats to fill* and the tab's badge (#545) |
 * | `getPostingGrid` | `GET /pools/{id}/posting-grid?sport&kind&who&level_low&level_high&week` — *Post a game*'s WHEN (#546, #558) |
 * | `getPostingSlot` | `GET /pools/{id}/posting-grid/slot?…&day&range` — a cell's sheet (#546, #558) |
 * | `postPost` | `POST /pools/{id}/posts` — *Post — you're In*: the poster's yes (#546, #558) |
 * | `getFriendsCard` | `GET /pools/{id}/friends-card?sport&kind&friend_ids…[&partner_id][&court_id&starts_at]` — a line-up's card (#750, #757) |
 * | `getFriendsCourts` | `GET /pools/{id}/friends-card/courts?sport&friend_ids…` — *Find a court* (#750, #757) |
 * | `postFriendsGame` | `POST /pools/{id}/friends-games` — *Send game and pay*: the court booked at once (#751, #759) |
 * | `postInvitationAcceptance` | `POST /bookings/{id}/invitation/acceptance` — *Accept* a friends game (#751, #759) |
 * | `postInvitationDecline` | `POST /bookings/{id}/invitation/decline` — *Not this time* on a friends game (#751, #759) |
 * | `postCallOff` | `POST /bookings/{id}/call-off` — the sender's *Call it off*, before the cut-off (#751, #759) |
 * | `postSeatInvitation` | `POST /bookings/{id}/seats/{seat_of}/invitations` — *Invite a friend* into an empty seat (#752, #760) |
 * | `postSeatOpening` | `POST /bookings/{id}/seats/{seat_of}/opening` — the sender's *Open to {group}*, before the cut-off (#752, #760) |
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
 * **Deal this group now** (Q127, ADR-0201 §5) — the card-builder's own batch for the pool, every
 * sport it plays; `204` once it has been applied, and a repeat deals nothing new. `pool_not_found`
 * for no such group and for one the reader is not in, as the deck's.
 */
export function postDeal(poolId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `/api/v1/pools/${encodeURIComponent(poolId)}/deal`,
    authenticated: true,
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
 * **Needs your answer went for good** (#815, #819; ADR-0205 §3) — `watermark` is `GET /home`'s
 * `needs_your_answer.watermark` from the read the sheet was last drawn from, as served: everything
 * that arrived up to it is seen on every phone. `204`, also for a watermark no later than the last
 * visit's, which never moves it back — so a repeat is safe. `watermark_in_the_future` (400) for one
 * past the server's clock, which no read served.
 */
export function postNeedsYourAnswerVisit(
  body: Schemas['NeedsYourAnswerVisitRequest'],
): Promise<void> {
  return httpRequest({
    method: 'POST',
    path: '/api/v1/players/me/needs-your-answer/visit',
    body,
    authenticated: true,
  });
}

/**
 * **A booked game in detail**, for a player in it, or for a member its open seat is offered to, who
 * reads it from outside (`rescue`, #545).
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
 * **Leave the game** (#544) — nothing taken before the club's cut-off, the hold on the card let go
 * (#637); refunded less the fee kept only when somebody takes the seat after it; and the yes
 * withdrawn while one payment is awaited (#625). `game_has_started` and `booking_is_called_off` (409)
 * where there is nothing to leave. Not retried: it moves money.
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

/**
 * **The friends card** (#750, #757) — a fixed line-up's card on a group's Friends tab: the sides,
 * the forecast, the overlap and a court, the query spelled by `toFriendsCardQuery`. Nothing is
 * recorded. `pool_not_found` (404) for no such group or one the reader is not in;
 * `not_a_friend`, `no_level`, `cannot_play_together` and `court_hour_not_for_sale` (409);
 * `block_state_unavailable` (503).
 */
export function getFriendsCard(
  poolId: string,
  query: string,
  { signal }: Cancellable = {},
): Promise<Schemas['FriendsCardResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/pools/${encodeURIComponent(poolId)}/friends-card?${query}`,
    authenticated: true,
    signal,
  });
}

/**
 * ***Find a court*** (#750, #757) — every court the line-up could take in the next 14 days, soonest
 * first, each with who is free. The card's refusals, less the court's.
 */
export function getFriendsCourts(
  poolId: string,
  query: string,
  { signal }: Cancellable = {},
): Promise<Schemas['FriendsCourtsResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/pools/${encodeURIComponent(poolId)}/friends-card/courts?${query}`,
    authenticated: true,
    signal,
  });
}

/**
 * ***Send game and pay*** (#751, #759) — the friends card as it was read, and how to pay: **the court
 * is booked at once**, the sender's share and a cover for every other seat held on their card, all
 * or nothing. Nothing booked when a payment was refused: `your_payments` names each to confirm, and
 * the send again carries the `booking_id` it answered. The guards, in the sheet's order (409):
 * `payment_method_required`, `friends_games_waiting`, `you_play_then`, `games_per_week_booked`,
 * `court_just_taken`, `court_hour_not_for_sale`; and the card's own, `not_a_friend`, `no_level`,
 * `cannot_play_together`. **Not retried**: it books a court and holds money. **No
 * `Idempotency-Key`**, because the server refuses the duplicate: a second send at an hour the sender
 * now plays is `you_play_then`, and a send again under a `booking_id` that booked answers what it
 * booked (#751) — the busy button is only what keeps the player from asking.
 */
export function postFriendsGame(
  poolId: string,
  body: Schemas['SendFriendsGameRequest'],
): Promise<Schemas['FriendsGameSentResponse']> {
  return httpRequest({
    method: 'POST',
    path: `${poolPath(poolId)}/friends-games`,
    authenticated: true,
    body,
  });
}

/**
 * ***Accept and pay 25 zł*** — or, with *Whole court*, *Accept* (#751, #759): the reader In, their
 * share held with *Split*, or `your_payment` to confirm in the app. `invitation_not_waiting`,
 * `booking_is_called_off`, `game_has_started`, `you_play_then`, `games_per_week_booked` and
 * `payment_method_required` (409). A second accept answers the same; not retried all the same.
 */
export function postInvitationAcceptance(
  bookingId: string,
): Promise<Schemas['FriendsGameAnswerResponse']> {
  return httpRequest({
    method: 'POST',
    path: `${bookingPath(bookingId)}/invitation/acceptance`,
    authenticated: true,
  });
}

/** ***Not this time*** on a friends game (#751, #759) — the seat empty; a second records nothing. */
export function postInvitationDecline(bookingId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${bookingPath(bookingId)}/invitation/decline`,
    authenticated: true,
  });
}

/**
 * ***Call it off*** — the sender's, before the club's cut-off (#751, #759): every hold and cover let
 * go, the court the club's again, everybody told. `cut_off_has_passed`, `booking_is_called_off`,
 * `game_has_started` (409); `booking_not_found` (404) for a game the reader did not send.
 */
export function postCallOff(bookingId: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${bookingPath(bookingId)}/call-off`,
    authenticated: true,
  });
}

function seatPath(bookingId: string, seatOf: string): string {
  return `${bookingPath(bookingId)}/seats/${encodeURIComponent(seatOf)}`;
}

/**
 * ***Invite a friend*** into an empty seat (#752, #760) — anybody In, one of their own friends, before
 * the cut-off or after it: the friend's invitation is a FRIENDS GAME card on Home for 24 hours. The
 * first to accept, or the first rescue, takes the seat. `seat_just_taken`, `already_on_the_game`,
 * `not_a_friend`, `no_level`, `cannot_play_together`, `friend_plays_then`, `friends_week_is_full`,
 * `booking_is_called_off`, `game_has_started` (409); `booking_not_found` (404). Not retried, as
 * every write is; a second invitation of the same friend is refused `already_on_the_game`.
 */
export function postSeatInvitation(
  bookingId: string,
  seatOf: string,
  body: Schemas['SeatInvitationRequest'],
): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${seatPath(bookingId, seatOf)}/invitations`,
    authenticated: true,
    body,
  });
}

/**
 * ***Open to {group}*** (#752, #760) — the sender puts an empty seat to the group before the cut-off:
 * a rescue from then on. Opened already, nothing more is recorded. `seat_just_taken`,
 * `cut_off_has_passed`, `booking_is_called_off`, `game_has_started` (409); `booking_not_found` (404)
 * for a game the reader did not send or no longer covers.
 */
export function postSeatOpening(bookingId: string, seatOf: string): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `${seatPath(bookingId, seatOf)}/opening`,
    authenticated: true,
  });
}

/** What the four controls ask — the post's body without its court hour (#546). */
export type PostingQuery = Omit<Schemas['PostRequest'], 'club_id' | 'starts_at'>;

/** The controls as a query string — a bound only once it has been narrowed. */
function postingQuery(ask: PostingQuery): string {
  const bounds = [
    ask.level_low === undefined || ask.level_low === null ? '' : `&level_low=${ask.level_low}`,
    ask.level_high === undefined || ask.level_high === null ? '' : `&level_high=${ask.level_high}`,
  ].join('');
  return `sport=${ask.sport}&kind=${ask.kind}&who=${ask.who}${bounds}`;
}

function poolPath(poolId: string): string {
  return `/api/v1/pools/${encodeURIComponent(poolId)}`;
}

/**
 * **WHEN** on *Post a game* — one week of 7 days × Morning / Afternoon / Evening for what the
 * controls hold (#546). Nothing is recorded. `level_range_too_wide`, `level_range_inverted` and
 * `mixed_pairs_only_in_doubles` (400) for an ask the controls should never send;
 * `not_rated_in_the_sport` and `who_leaves_you_out` (409); `pool_not_found` (404).
 */
export function getPostingGrid(
  poolId: string,
  ask: PostingQuery,
  week: 1 | 2,
  { signal }: Cancellable = {},
): Promise<Schemas['PostingGridResponse']> {
  return httpRequest({
    method: 'GET',
    path: `${poolPath(poolId)}/posting-grid?${postingQuery(ask)}&week=${week}`,
    authenticated: true,
    signal,
  });
}

/**
 * **A cell's sheet** — its fits, its free courts home club first, and what is already happening
 * there (#546). Nothing is recorded; refused as the grid is.
 */
export function getPostingSlot(
  poolId: string,
  ask: PostingQuery,
  day: string,
  range: Schemas['DayRange'],
  { signal }: Cancellable = {},
): Promise<Schemas['PostingSlotResponse']> {
  return httpRequest({
    method: 'GET',
    path: `${poolPath(poolId)}/posting-grid/slot?${postingQuery(ask)}&day=${day}&range=${range}`,
    authenticated: true,
    signal,
  });
}

/**
 * ***Post — you're In*** (#546): the poster's yes, dealt as up to three versions to their best fits
 * free then. The guards, in the button's order (409): `payment_method_required`,
 * `live_posts_exhausted`, `games_per_week_booked`; then `you_play_then`,
 * `nobody_fits_then` and `court_hour_not_for_sale`. **Not retried**: a second post is a second game.
 * **No `Idempotency-Key`**: the button is busy while one is in flight, and a second post at an hour
 * the poster already plays is refused (`you_play_then`) — a duplicate is refused, never booked.
 */
export function postPost(
  poolId: string,
  body: Schemas['PostRequest'],
): Promise<Schemas['PostedResponse']> {
  return httpRequest({
    method: 'POST',
    path: `${poolPath(poolId)}/posts`,
    authenticated: true,
    body,
  });
}

function bookingPath(bookingId: string): string {
  return `/api/v1/bookings/${encodeURIComponent(bookingId)}`;
}

function proposalPath(proposalId: string): string {
  return `/api/v1/proposals/${encodeURIComponent(proposalId)}`;
}
