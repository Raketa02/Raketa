/**
 * **Posting a game, as the backend answers it** — the grid, a cell's sheet and the post
 * (`GET /pools/{id}/posting-grid`, `…/posting-grid/slot`, `POST /pools/{id}/posts`; #546), for the
 * suites that walk *Post a game* ([#558](https://github.com/Raketa02/Raketa/issues/558)).
 *
 * The grid is read at `DECK_READ_AT` — Wednesday 30 September 2026, 10:00 in Warsaw — so week one
 * runs Wednesday 30 September to Tuesday 6 October and week two the seven days after. **Every cell
 * is dead unless a suite lights it**: `postingGrid({ cells: { '2026-10-03:EVENING': HOT } })`.
 * The people are the deck's (`test-support/groupDeck`), and the courts are its two clubs.
 *
 * The transport drops the query string before matching, so one stub answers every ask; a suite
 * that needs to know what was asked reads it off the request (`askedOf`).
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { DECK_READ_AT, KAROL, KUBA, ZOFIA, ANIA, EWA, youTile } from './groupDeck';
import { json, type RecordedRequest, type Transport, type Wire } from './transport';

type Cell = Wire['PostingCellSchema'];

export function postingGridPath(groupId: string): string {
  return `/api/v1/pools/${groupId}/posting-grid`;
}

export function postingSlotPath(groupId: string): string {
  return `/api/v1/pools/${groupId}/posting-grid/slot`;
}

export function postsPath(groupId: string): string {
  return `/api/v1/pools/${groupId}/posts`;
}

/** The query a request carried, as strings — `sport`, `kind`, `who`, `level_low`, `week`, `day`… */
export function askedOf(request: RecordedRequest): Readonly<Record<string, string>> {
  const query = request.url.split('?')[1] ?? '';
  return Object.fromEntries(new URLSearchParams(query));
}

const RANGES: Wire['DayRange'][] = ['MORNING', 'AFTERNOON', 'EVENING'];

/** The first hour of each range, in Warsaw (UTC+2 until 25 October). */
const RANGE_START: Readonly<Record<Wire['DayRange'], string>> = {
  MORNING: '06:00',
  AFTERNOON: '13:00',
  EVENING: '17:00',
};

/** `2026-09-30` plus `n` days. */
export function dayAfterRead(n: number): string {
  const day = new Date(Date.UTC(2026, 8, 30 + n));
  return day.toISOString().slice(0, 10);
}

/** A best hour in a day's range — the range's own hour in the fixtures. */
export function bestHour(day: string, range: Wire['DayRange']): string {
  return `${day}T${RANGE_START[range]}:00Z`;
}

// --- The looks, as the server says them ------------------------------------

/** *Few, no court* — two fit, no court (mock 25). */
export const FEW: Partial<Cell> = { fits_free: 2, court_free: false, full_game: false };
/** *Enough, no court* — a full game's worth, no court (mock 26). */
export const ENOUGH: Partial<Cell> = { fits_free: 4, court_free: false, full_game: true };
/** *Court, thin* — a court, two fit (mock 27). */
export const THIN: Partial<Cell> = { fits_free: 2, court_free: true, full_game: false };
/** *Hot* — a court and five fit (mocks 23, 28). */
export const HOT: Partial<Cell> = { fits_free: 5, court_free: true, full_game: true };

/** One cell — dead unless told otherwise. */
export function postingCell(range: Wire['DayRange'], day: string, extra: Partial<Cell> = {}): Cell {
  return {
    range,
    fits_free: 0,
    best_starts_at: bestHour(day, range),
    court_free: false,
    full_game: false,
    outside_your_hours: false,
    past: false,
    happening: false,
    ...extra,
  };
}

/**
 * **A week of the grid** — every cell dead but those named `day:RANGE`. Padel, Competitive, anybody,
 * the engine's window 2,56–2,86 and nothing narrowed, three seats open.
 */
export function postingGrid({
  week = 1,
  cells = {},
  ...extra
}: Partial<Omit<Wire['PostingGridResponse'], 'days' | 'week'>> & {
  readonly week?: 1 | 2;
  readonly cells?: Readonly<Record<string, Partial<Cell>>>;
} = {}): Wire['PostingGridResponse'] {
  const first = week === 1 ? 0 : 7;
  return {
    pool_id: 'a0000000-0000-4000-8000-000000000011',
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    who: 'ANYONE',
    week,
    read_at: new Date(DECK_READ_AT).toISOString(),
    level_range: { low: 2.56, high: 2.86 },
    engine_level_range: { low: 2.56, high: 2.86 },
    open_seats: 3,
    days: Array.from({ length: 7 }, (_, at) => {
      const day = dayAfterRead(first + at);
      return {
        day,
        is_today: first + at === 0,
        cells: RANGES.map((range) => postingCell(range, day, cells[`${day}:${range}`])),
      };
    }),
    ...extra,
  };
}

/** Serve the grid — fixed, or read off the request (both weeks, or what was asked). */
export function stubPostingGrid(
  transport: Transport,
  groupId: string,
  grid:
    | Wire['PostingGridResponse']
    | ((request: RecordedRequest) => Wire['PostingGridResponse'] | Response) = postingGrid(),
): void {
  transport.on('GET', postingGridPath(groupId), (request) => {
    if (typeof grid !== 'function') return json(grid);
    const answer = grid(request);
    return answer instanceof Response ? answer : json(answer);
  });
}

// --- A cell's sheet ---------------------------------------------------------

/** A fit, from a deck tile — their Level and a forecast. */
export function slotFit(tile: Wire['DeckTileSchema'], pct: number): Wire['SlotFitSchema'] {
  return {
    player_id: tile.player_id,
    nickname: tile.nickname,
    photo_id: tile.photo_id,
    photo_url: tile.photo_url,
    level: tile.level,
    friend: tile.friend,
    forecast: { pct, provisional: false },
  };
}

/** Mock 34's five: Karol, Zofia, Ania, Ewa, Kuba. */
export const FITS: Wire['SlotFitSchema'][] = [
  slotFit(KAROL(), 93),
  slotFit(ZOFIA(), 95),
  slotFit(ANIA(), 99),
  slotFit(EWA(), 91),
  slotFit(KUBA(), 96),
];

export const OGRODY = { id: 'b0000000-0000-4000-8000-000000000002', name: 'Ogrody 33' };
export const BONARKA = { id: 'b0000000-0000-4000-8000-000000000001', name: 'Bonarka Arena' };

/**
 * **A free court** — mock 34's first: Ogrody 33, the home club, 2,4 km, Saturday 17:00, 27 zł if it
 * fills, book by Saturday 15:00, two courts and four fits free then.
 */
export function freeCourt(extra: Partial<Wire['FreeCourtSchema']> = {}): Wire['FreeCourtSchema'] {
  return {
    club: OGRODY,
    home_club: true,
    // Read by no screen yet: the home club is never full of itself (#746).
    home_club_full: false,
    distance_km: 2.4,
    starts_at: '2026-10-03T15:00:00Z',
    share_grosze: 2700,
    book_by: '2026-10-03T13:00:00Z',
    courts: 2,
    fits_free: 4,
    ...extra,
  };
}

let filling = 0;

/** **Somebody else's post still filling** — Kuba's, Saturday 17:00 at Bonarka, him In, two seats open. */
export function postStillFilling(
  extra: Partial<Wire['PostStillFillingSchema']> = {},
): Wire['PostStillFillingSchema'] {
  filling += 1;
  return {
    proposal_id: `aa000000-0000-4000-8000-${String(filling).padStart(12, '0')}`,
    kind: 'COMPETITIVE',
    starts_at: '2026-10-03T15:00:00Z',
    club: BONARKA,
    share_grosze: 3200,
    book_by: '2026-10-03T13:00:00Z',
    challenger: { player_id: KUBA().player_id, nickname: KUBA().nickname },
    people_in: [KUBA({ is_in: true }), ANIA({ is_in: true })],
    open_seats: 2,
    ...extra,
  };
}

/** **A cell's sheet** — Saturday evening: hot, mock 34's five fits and one free court. */
export function postingSlot(
  extra: Partial<Wire['PostingSlotResponse']> = {},
): Wire['PostingSlotResponse'] {
  const day = extra.day ?? '2026-10-03';
  const range = extra.range ?? 'EVENING';
  return {
    pool_id: 'a0000000-0000-4000-8000-000000000011',
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    who: 'ANYONE',
    day,
    range,
    read_at: new Date(DECK_READ_AT).toISOString(),
    level_range: { low: 2.56, high: 2.86 },
    open_seats: 3,
    cell: postingCell(range, day, HOT),
    fits: FITS,
    free_courts: [freeCourt()],
    rescues: [],
    posts: [],
    ...extra,
  };
}

/** Serve a cell's sheet — fixed, or read off the request. */
export function stubPostingSlot(
  transport: Transport,
  groupId: string,
  slot:
    | Wire['PostingSlotResponse']
    | ((request: RecordedRequest) => Wire['PostingSlotResponse'] | Response) = postingSlot(),
): void {
  transport.on('GET', postingSlotPath(groupId), (request) => {
    if (typeof slot !== 'function') return json(slot);
    const answer = slot(request);
    return answer instanceof Response ? answer : json(answer);
  });
}

/** The post's answer — dealt in one version to five fits, three seats open. */
export function postedAnswer(extra: Partial<Wire['PostedResponse']> = {}): Wire['PostedResponse'] {
  return {
    proposal_id: 'ab000000-0000-4000-8000-000000000001',
    versions: 1,
    dealt_to: 5,
    open_seats: 3,
    ...extra,
  };
}

/** The reader's own tile, In — the poster's square on their own post. */
export const POSTER = youTile({ is_in: true });
