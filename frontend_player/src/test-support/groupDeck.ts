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
}
