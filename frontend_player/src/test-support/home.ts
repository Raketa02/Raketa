/**
 * **Home's booked games and a booked game's details, as the wire answers them** — the fixtures the
 * Home and details suites build on (#556).
 *
 * One game throughout: *you + Piotr against Inés + Bartek* at Bonarka Arena, Court 2, on Saturday 3
 * October 2026 at 16:00 in Warsaw, booked, every share held until the club's cut-off on Friday at
 * 16:00 and free to leave until then (Q113). Each suite moves only what it is about — the status,
 * the money, the day — off these.
 */

import type { Transport, Wire } from './transport';
import { json } from './transport';
import { GATE_USER, bookingPath, stubHome } from './onboardingRouter';

/** Thursday 1 October 2026, 10:00 in Warsaw — the instant Home and the details were read. */
export const HOME_READ_AT = '2026-10-01T08:00:00Z';

/** Saturday 3 October, 16:00 in Warsaw — the court hour. */
export const BOOKED_STARTS_AT = '2026-10-03T14:00:00Z';
export const BOOKED_ENDS_AT = '2026-10-03T15:00:00Z';

/** Friday 2 October, 16:00 in Warsaw — the club's cut-off. */
export const BOOKED_CUT_OFF = '2026-10-02T14:00:00Z';

export const BOOKING = '3f2b8c1e-0000-4000-8000-0000000000b1';
export const BOOKED_GAME = '3f2b8c1e-0000-4000-8000-0000000000a1';
export const BOOKED_ROOM = '3f2b8c1e-0000-4000-8000-0000000000c1';
const GROUP = '3f2b8c1e-0000-4000-8000-0000000000d1';
const CLUB = '3f2b8c1e-0000-4000-8000-0000000000e1';

export const PIOTR = '3f2b8c1e-0000-4000-8000-000000000101';
export const INES = '3f2b8c1e-0000-4000-8000-000000000102';
export const BARTEK = '3f2b8c1e-0000-4000-8000-000000000103';

function seat(
  playerId: string,
  name: string,
  level: number,
  extra: Partial<Wire['BookedTileSchema']> = {},
): Wire['BookedTileSchema'] {
  return {
    player_id: playerId,
    is_you: false,
    nickname: name,
    photo_id: null,
    photo_url: null,
    level,
    paid: false,
    friend: false,
    ...extra,
  };
}

/**
 * The four, the reader's side first and the reader first on it, as the wire orders them — each
 * *paid* once the shares are taken (`paid`), which is never before the cut-off (Q113).
 */
export function bookedSides({
  paid = false,
}: { readonly paid?: boolean } = {}): Wire['BookedSidesSchema'] {
  return {
    yours: [
      seat(GATE_USER.id, GATE_USER.nickname ?? 'Ada', 2.71, { is_you: true, paid }),
      seat(PIOTR, 'piotr.s', 2.95, { paid }),
    ],
    theirs: [seat(INES, 'ines.d', 3.4, { paid }), seat(BARTEK, 'bartek.l', 2.35, { paid })],
  };
}

/**
 * 28 zł a seat, **held** on the card until the club's cut-off on Friday at 16:00, free to leave
 * until then, and nothing refunded (Q113).
 */
export function bookedMoney(
  extra: Partial<Wire['BookedMoneySchema']> = {},
): Wire['BookedMoneySchema'] {
  return {
    share_grosze: 2800,
    paid: false,
    share_state: 'HELD',
    held_from: null,
    taken_at: BOOKED_CUT_OFF,
    free_to_leave_until: BOOKED_CUT_OFF,
    refunded_grosze: null,
    ...extra,
  };
}

/** The same 28 zł **taken** at the cut-off, as a read after it says (Q113). */
export function takenMoney(
  extra: Partial<Wire['BookedMoneySchema']> = {},
): Wire['BookedMoneySchema'] {
  return bookedMoney({ paid: true, share_state: 'TAKEN', free_to_leave_until: null, ...extra });
}

/** Nobody's money on the game — waiting for a payment, or called off (#637). */
export function unheldMoney(
  extra: Partial<Wire['BookedMoneySchema']> = {},
): Wire['BookedMoneySchema'] {
  return bookedMoney({ share_state: null, taken_at: null, free_to_leave_until: null, ...extra });
}

/** One card on Home. */
export function homeGame(extra: Partial<Wire['HomeGameSchema']> = {}): Wire['HomeGameSchema'] {
  return {
    booking_id: BOOKING,
    game_id: BOOKED_GAME,
    pool_id: GROUP,
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    status: 'BOOKED',
    called_off_reason: null,
    club_cancel_reason: null,
    uncounted_reason: null,
    open_seats: 0,
    needs_you: false,
    filling_again: false,
    starts_at: BOOKED_STARTS_AT,
    club: { id: CLUB, name: 'Bonarka Arena' },
    court_name: 'Court 2',
    indoor: true,
    sides: bookedSides(),
    money: bookedMoney(),
    payment_due_by: null,
    your_payment_due_by: null,
    time_to: null,
    friends_game: null,
    ...extra,
  };
}

/** Home with these cards, read at {@link HOME_READ_AT}. */
export function stubHomeGames(
  transport: Transport,
  games: readonly Wire['HomeGameSchema'][],
  extra: Partial<Wire['HomeResponse']> = {},
) {
  stubHome(transport, { read_at: HOME_READ_AT, games: [...games], ...extra });
}

/** The booked game in detail. */
export function bookingDetails(
  extra: Partial<Wire['BookingDetailsResponse']> = {},
): Wire['BookingDetailsResponse'] {
  return {
    booking_id: BOOKING,
    game_id: BOOKED_GAME,
    pool_id: GROUP,
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    read_at: HOME_READ_AT,
    status: 'BOOKED',
    called_off_reason: null,
    club_cancel_reason: null,
    uncounted_reason: null,
    open_seats: 0,
    needs_you: false,
    filling_again: false,
    starts_at: BOOKED_STARTS_AT,
    ends_at: BOOKED_ENDS_AT,
    where: { id: CLUB, name: 'Bonarka Arena', distance_km: 3.1 },
    court_name: 'Court 2',
    indoor: true,
    sides: bookedSides(),
    money: bookedMoney(),
    shows_forecast: true,
    leaving: { kind: 'BEFORE_THE_CUT_OFF', refund_grosze: null, card_fee_grosze: null },
    rescue: null,
    payment_due_by: null,
    your_payment_due_by: null,
    time_to: null,
    played_with: [],
    friends_game: null,
    ...extra,
  };
}

export function stubBooking(transport: Transport, details: Wire['BookingDetailsResponse']) {
  transport.on('GET', bookingPath(details.booking_id), () => json(details));
}

/** The room's members — the four on the court, as a booked game's room is opened with them. */
export function bookedMembers(): Wire['ConversationMemberSchema'][] {
  return [
    { player_id: GATE_USER.id, nickname: GATE_USER.nickname ?? 'Ada' },
    { player_id: PIOTR, nickname: 'piotr.s' },
    { player_id: INES, nickname: 'ines.d' },
    { player_id: BARTEK, nickname: 'bartek.l' },
  ];
}

/** The booked game's room as the Chats list carries it — filed under the booking, about its game. */
export function bookedRoomRow(): Wire['ConversationRowSchema'] {
  const members = bookedMembers();
  return {
    conversation_id: BOOKED_ROOM,
    booking_id: BOOKING,
    game_id: BOOKED_GAME,
    sport: 'PADEL',
    members,
    people: members,
    last_entry: null,
  };
}

/** The booked game's room opened, with nothing said in it yet. */
export function bookedRoom(): Wire['ConversationResponse'] {
  const members = bookedMembers();
  return {
    read_at: HOME_READ_AT,
    conversation_id: BOOKED_ROOM,
    booking_id: BOOKING,
    game_id: BOOKED_GAME,
    sport: 'PADEL',
    members,
    people: members,
    entries: [],
  };
}

/** The booked game's Game, as `GET /games` lists it — the hour still ahead, nothing entered. */
export function bookedGameOnTheList(extra: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: BOOKED_GAME,
    booking_id: BOOKING,
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: '2026-09-30T18:00:00Z',
    entry_closes_at: '2026-10-05T14:00:00Z',
    seats: [
      { side: 'A', player_id: GATE_USER.id, nickname: GATE_USER.nickname ?? 'Ada' },
      { side: 'A', player_id: PIOTR, nickname: 'piotr.s' },
      { side: 'B', player_id: INES, nickname: 'ines.d' },
      { side: 'B', player_id: BARTEK, nickname: 'bartek.l' },
    ],
    proposals: [],
    attendance: [],
    ...extra,
  };
}
