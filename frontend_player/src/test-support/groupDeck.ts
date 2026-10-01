/**
 * **A group's deck, as `GET /pools/{id}/deck` answers it** — the Games tab's read, for the suites
 * that open a group's page ([#553](https://github.com/Raketa02/Raketa/issues/553)).
 *
 * The pool is filed under the group's id, so the path is the group's. The transport drops the
 * query string before matching, so one stub answers both kinds; a suite that needs the two
 * segments to deal different cards reads the `kind` off the request (`kindAsked`).
 *
 * Every card here is built from the people below, in the mocks' own line-ups, with the times put
 * where a test can reason about them: **the read happens at `DECK_READ_AT`** — the suites set the
 * fake clock there — and a card's deadline is a number of hours after it.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { GATE_USER } from './onboardingRouter';
import { json, type RecordedRequest, type Transport, type Wire } from './transport';

/** Wednesday 30 September 2026, 10:00 in Warsaw — the instant every suite's deck is read at. */
export const DECK_READ_AT = Date.parse('2026-09-30T08:00:00Z');

const HOUR = 3_600_000;

/** An instant `hours` after the deck is read. */
export function hoursAfterRead(hours: number): string {
  return new Date(DECK_READ_AT + hours * HOUR).toISOString();
}

export function deckPath(groupId: string): string {
  return `/api/v1/pools/${groupId}/deck`;
}

export function yesPath(proposalId: string): string {
  return `/api/v1/proposals/${proposalId}/yes`;
}

export function noPath(proposalId: string): string {
  return `/api/v1/proposals/${proposalId}/no`;
}

/** *I'm in* on a rescue — the booking's seat (#545). */
export function seatsPath(bookingId: string): string {
  return `/api/v1/bookings/${bookingId}/seats`;
}

/** A no to a *Seat open* card — the booking's (#545). */
export function rescueNoPath(bookingId: string): string {
  return `/api/v1/bookings/${bookingId}/no`;
}

/** One game still filling, in detail (#542, #557). */
export function proposalPath(proposalId: string): string {
  return `/api/v1/proposals/${proposalId}`;
}

/** Which kind a deck request asked for. */
export function kindAsked(request: RecordedRequest): Wire['SearchMode'] | undefined {
  const kind = /[?&]kind=([A-Z_]+)/.exec(request.path)?.[1];
  return kind === 'COMPETITIVE' || kind === 'FOR_FUN' ? kind : undefined;
}

type Tile = Wire['DeckTileSchema'];

function tile(n: number, name: string, level: number, extra: Partial<Tile> = {}): Tile {
  return {
    player_id: `d0000000-0000-4000-8000-00000000000${n}`,
    is_you: false,
    name,
    photo_id: null,
    photo_url: null,
    level,
    is_in: false,
    paid: false,
    ...extra,
  };
}

/** The reader's own tile — the signed-in player, as the gate knows them. */
export function youTile(extra: Partial<Tile> = {}): Tile {
  return {
    ...tile(0, GATE_USER.name ?? 'Ada Lovelace', 2.71),
    player_id: GATE_USER.id,
    is_you: true,
    ...extra,
  };
}

export const KAROL = (extra: Partial<Tile> = {}) => tile(1, 'Karol Tomaszewski', 2.75, extra);
export const ZOFIA = (extra: Partial<Tile> = {}) => tile(2, 'Zofia Bielecka', 2.69, extra);
export const ANIA = (extra: Partial<Tile> = {}) => tile(3, 'Ania Kowalska', 2.68, extra);
export const KUBA = (extra: Partial<Tile> = {}) => tile(4, 'Kuba Wiśniewski', 2.8, extra);
export const EWA = (extra: Partial<Tile> = {}) => tile(5, 'Ewa Majewska', 2.6, extra);

/** Twenty-one cells, Monday first and morning first, every one dark but the ones named. */
export function overlapCells(
  lit: Readonly<Record<string, Wire['OverlapShade']>> = {},
): Wire['OverlapCellSchema'][] {
  const ranges: Wire['DayRange'][] = ['MORNING', 'AFTERNOON', 'EVENING'];
  return [1, 2, 3, 4, 5, 6, 7].flatMap((day) =>
    ranges.map((range) => ({ day, range, shade: lit[`${day}:${range}`] ?? 'DARK' })),
  );
}

let dealt = 0;

/**
 * **A Picked for you card** — mock 6's line-up: you and Zofia against Ania and Ewa, nobody In, a
 * free vote on a Saturday afternoon at Bonarka Arena, its book-by two days off.
 */
export function deckCard(extra: Partial<Wire['DeckCardSchema']> = {}): Wire['DeckCardSchema'] {
  dealt += 1;
  return {
    proposal_id: `c0000000-0000-4000-8000-${String(dealt).padStart(12, '0')}`,
    type: 'PICKED_FOR_YOU',
    kind: 'COMPETITIVE',
    challenger: null,
    // Saturday 3 October, 16:00 in Warsaw.
    starts_at: '2026-10-03T14:00:00Z',
    club: { id: 'b0000000-0000-4000-8000-000000000001', name: 'Bonarka Arena' },
    share_grosze: 3200,
    deadline: hoursAfterRead(48),
    in_count: 0,
    version_count: 1,
    open_seats_after_your_yes: 3,
    court: 'COURT_AVAILABLE',
    court_name: null,
    no_free_cancellation: false,
    club_confirms: false,
    sides: { yours: [youTile(), ZOFIA()], theirs: [ANIA(), EWA()] },
    forecast: { pct: 87, provisional: false },
    overlap: {
      grade: 'SLIM',
      cells: overlapCells({ '6:AFTERNOON': 'BRIGHT', '5:EVENING': 'DIM' }),
      game: { day: 6, range: 'AFTERNOON' },
    },
    ...extra,
  };
}

/**
 * **A Seat open card** — mock 2's rescue: Karol and Ania paid on one side, Kuba paid on the other,
 * and you in the seat that opened, on Kuba's side — the last seat, so *You complete it*. The court is
 * booked (Court 6 at Ogrody 33, Saturday 16:00), the share 27 zł, and the card's deadline is the
 * cut-off, 21 hours off. Its id is the booking's.
 */
export function rescueCard(extra: Partial<Wire['DeckCardSchema']> = {}): Wire['DeckCardSchema'] {
  return deckCard({
    type: 'SEAT_OPEN',
    court: 'BOOKED',
    court_name: 'Court 6',
    club: { id: 'b0000000-0000-4000-8000-000000000002', name: 'Ogrody 33' },
    share_grosze: 2700,
    deadline: hoursAfterRead(21),
    open_seats_after_your_yes: 0,
    sides: {
      yours: [youTile(), KUBA({ paid: true })],
      theirs: [KAROL({ paid: true }), ANIA({ paid: true })],
    },
    forecast: { pct: 91, provisional: false },
    ...extra,
  });
}

/**
 * **A card's game, as its details read it** (`GET /proposals/{id}`) — the same game, sides and
 * overlap, in the crew's group, Bonarka 3,1 km away, still filling: *I'm in* and *Not this time*
 * for a reader still deciding, *Withdraw* once their tile is In.
 */
export function proposalDetails(
  card: Wire['DeckCardSchema'],
  extra: Partial<Wire['ProposalDetailsResponse']> = {},
): Wire['ProposalDetailsResponse'] {
  const youIn = card.sides.yours.some((tile) => tile.is_you && tile.is_in);
  return {
    proposal_id: card.proposal_id,
    pool_id: 'a0000000-0000-4000-8000-000000000005',
    type: card.type,
    kind: card.kind,
    sport: 'PADEL',
    challenger: card.challenger,
    read_at: new Date(DECK_READ_AT).toISOString(),
    status: 'FILLING',
    actions: youIn ? ['WITHDRAW'] : ['YES', 'NO'],
    your_payment: null,
    in_count: card.in_count,
    seats: 4,
    starts_at: card.starts_at,
    where: { ...card.club, distance_km: 3.1 },
    share_grosze: card.share_grosze,
    book_by: card.deadline,
    no_free_cancellation: card.no_free_cancellation,
    club_confirms: card.club_confirms,
    sides: card.sides,
    forecast: card.forecast,
    overlap: card.overlap,
    ...extra,
  };
}

/** **The card's game with your yes in it** — your tile In, one more In, *Withdraw*. */
export function withYourYes(
  details: Wire['ProposalDetailsResponse'],
): Wire['ProposalDetailsResponse'] {
  const mark = (tiles: Tile[]) =>
    tiles.map((tile) => (tile.is_you ? { ...tile, is_in: true } : tile));
  return {
    ...details,
    in_count: details.in_count + 1,
    actions: ['WITHDRAW'],
    sides: { yours: mark(details.sides.yours), theirs: mark(details.sides.theirs) },
  };
}

/** Serve a game's details — fixed, or read off the suite's own state at each request. */
export function stubProposal(
  transport: Transport,
  proposalId: string,
  details: Wire['ProposalDetailsResponse'] | (() => Wire['ProposalDetailsResponse']),
): void {
  transport.on('GET', proposalPath(proposalId), () =>
    json(typeof details === 'function' ? details() : details),
  );
}

/** A group's Fill in tab — `GET /pools/{id}/fill-in?sport` (#545). */
export function fillInPath(groupId: string): string {
  return `/api/v1/pools/${groupId}/fill-in`;
}

/** A booked court's seat, from a deck tile — paid. */
function seatOf(tile: Tile): Wire['BookedTileSchema'] {
  return {
    player_id: tile.player_id,
    is_you: false,
    name: tile.name,
    photo_id: tile.photo_id,
    photo_url: tile.photo_url,
    level: tile.level,
    paid: true,
  };
}

let rescued = 0;

/**
 * **A *Seats to fill* row** — mock 12's: padel on Saturday 3 October at 16:00 at Ogrody 33, Court 6,
 * Karol, Ania and Kuba paid and one seat open, 27 zł, filling by the cut-off on Friday at 16:00.
 */
export function seatToFill(
  extra: Partial<Wire['SeatToFillSchema']> = {},
): Wire['SeatToFillSchema'] {
  rescued += 1;
  return {
    booking_id: `e0000000-0000-4000-8000-${String(rescued).padStart(12, '0')}`,
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    starts_at: '2026-10-03T14:00:00Z',
    club: { id: 'b0000000-0000-4000-8000-000000000002', name: 'Ogrody 33' },
    court_name: 'Court 6',
    share_grosze: 2700,
    open_seats: 1,
    deadline: '2026-10-02T14:00:00Z',
    fills_by_the_cut_off: true,
    players: [seatOf(KAROL()), seatOf(ANIA()), seatOf(KUBA())],
    ...extra,
  };
}

/** The tab's read: these rows, the badge counting them, read at {@link DECK_READ_AT}. */
export function fillIn(rows: readonly Wire['SeatToFillSchema'][] = []): Wire['FillInResponse'] {
  return {
    pool_id: 'a0000000-0000-4000-8000-000000000005',
    sport: 'PADEL',
    read_at: new Date(DECK_READ_AT).toISOString(),
    badge: rows.length,
    seats_to_fill: [...rows],
  };
}

/** Serve a group's Fill in — fixed, or read off the suite's own state at each request. */
export function stubFillIn(
  transport: Transport,
  groupId: string,
  read: Wire['FillInResponse'] | (() => Wire['FillInResponse']) = fillIn(),
): void {
  transport.on('GET', fillInPath(groupId), () => json(typeof read === 'function' ? read() : read));
}

let said = 0;

/**
 * **A live yes** — mock 48's row: padel on Saturday at 15:00 at Bonarka Arena, a 28 zł share, its
 * book-by a day off — a yes said in the group whose id is `pool_id`.
 */
export function liveYes(extra: Partial<Wire['LiveYesSchema']> = {}): Wire['LiveYesSchema'] {
  said += 1;
  return {
    proposal_id: `f0000000-0000-4000-8000-${String(said).padStart(12, '0')}`,
    pool_id: 'a0000000-0000-4000-8000-000000000005',
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    // Saturday 3 October, 15:00 in Warsaw.
    starts_at: '2026-10-03T13:00:00Z',
    club: { id: 'b0000000-0000-4000-8000-000000000001', name: 'Bonarka Arena' },
    share_grosze: 2800,
    book_by: hoursAfterRead(24),
    ...extra,
  };
}

/** A deck with both segments, nothing dealt, nothing capped — the tab's quietest answer. */
export function groupDeck(
  extra: Partial<Wire['GroupDeckResponse']> = {},
): Wire['GroupDeckResponse'] {
  const cards = extra.cards ?? [];
  return {
    pool_id: 'a0000000-0000-4000-8000-000000000011',
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    segments: [
      { kind: 'COMPETITIVE', count: cards.filter((card) => card.kind === 'COMPETITIVE').length },
      { kind: 'FOR_FUN', count: cards.filter((card) => card.kind === 'FOR_FUN').length },
    ],
    games_badge: cards.filter((card) => card.in_count > 0).length,
    games_per_week: 2,
    capped_weeks: [],
    cards,
    ...extra,
  };
}

/**
 * **Serve a group's deck** — the same answer for both kinds, or one answer per kind. The default
 * is the quiet deck, which leaves the Games tab on the starting cards it drew before #553.
 *
 * **And the group's Fill in, empty** (#557): the page reads it for the Fill in tab's badge whichever
 * tab is open, so every suite that opens a group page would otherwise fail at the socket. A suite
 * about Fill in serves its own afterwards (`stubFillIn`).
 */
export function stubGroupDeck(
  transport: Transport,
  groupId: string,
  deck:
    | Wire['GroupDeckResponse']
    | ((kind: Wire['SearchMode'] | undefined) => Wire['GroupDeckResponse']) = groupDeck(),
): void {
  transport.on('GET', deckPath(groupId), (request) =>
    json(typeof deck === 'function' ? deck(kindAsked(request)) : deck),
  );
  stubFillIn(transport, groupId);
}
