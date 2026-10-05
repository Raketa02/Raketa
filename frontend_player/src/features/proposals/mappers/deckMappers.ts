/**
 * **The group deck, off the wire** — the wire boundary for the Games tab. Generated types stop here
 * and in `api/`.
 *
 * Three narrowings, each the one the rest of the app makes: a `null` becomes an absent field, so a
 * tile with no photograph draws its poster and an unrated one draws no Level; a weekday the wire
 * spells as an ISO number is held to the week's own union, and a cell outside it is dropped rather
 * than drawn on a day that does not exist; and the kind is read into the switch's spelling
 * (`domain/vocabulary`).
 */

import type { components } from '@/generated/schema';
import { WEEKDAYS, type Weekday } from '@/shared/vocabulary/week';

import type {
  CappedWeek,
  DeckCard,
  DeckPerson,
  DeckSegment,
  GroupDeck,
  Overlap,
  OverlapCell,
} from '../domain/deck';
import type { GameKind } from '../domain/vocabulary';

type Schemas = components['schemas'];

/** The switch's spelling of the wire's two modes — both ways, each a `Record` over its union. */
const KIND_BY_WIRE: Readonly<Record<Schemas['SearchMode'], GameKind>> = {
  COMPETITIVE: 'competitive',
  FOR_FUN: 'forFun',
};

const WIRE_BY_KIND: Readonly<Record<GameKind, Schemas['SearchMode']>> = {
  competitive: 'COMPETITIVE',
  forFun: 'FOR_FUN',
};

export function toWireKind(kind: GameKind): Schemas['SearchMode'] {
  return WIRE_BY_KIND[kind];
}

export function toKind(wire: Schemas['SearchMode']): GameKind {
  return KIND_BY_WIRE[wire];
}

/** A card's club — the name left off for a club that no longer exists. A live yes's too. */
export function toClub(wire: {
  readonly id: string;
  readonly name: string | null;
}): DeckCard['club'] {
  return { id: wire.id, ...(wire.name === null ? {} : { name: wire.name }) };
}

function toWeekday(day: number): Weekday | undefined {
  return WEEKDAYS.find((weekday) => weekday === day);
}

/** One person on a card — a post's people In too (#558). */
export function toPerson(wire: Schemas['DeckTileSchema']): DeckPerson {
  return {
    playerId: wire.player_id,
    isYou: wire.is_you,
    isIn: wire.is_in,
    // Paid is a rescue's people's; a card still filling draws IN or nothing.
    ...(wire.paid ? { paid: true } : {}),
    ...(wire.name === null ? {} : { name: wire.name }),
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    ...(wire.level === null ? {} : { level: wire.level }),
  };
}

function toCell(wire: Schemas['OverlapCellSchema']): OverlapCell | undefined {
  const day = toWeekday(wire.day);
  return day === undefined ? undefined : { day, range: wire.range, shade: wire.shade };
}

/** The two sides, as a card and a game's details both carry them. */
export function toDeckSides(wire: Schemas['DeckSidesSchema']): DeckCard['sides'] {
  return { yours: wire.yours.map(toPerson), theirs: wire.theirs.map(toPerson) };
}

/** A challenge's poster — the name left off for one who can no longer be named. */
export function toChallenger(
  wire: Schemas['DeckChallengerSchema'] | null,
): Pick<DeckCard, 'challenger'> {
  if (wire === null) return {};
  return {
    challenger: {
      playerId: wire.player_id,
      ...(wire.name === null ? {} : { name: wire.name }),
    },
  };
}

/**
 * The overlap grid — or nothing, for a game cell that names no weekday: the ring would have
 * nowhere to go.
 */
export function toOverlap(wire: Schemas['DeckOverlapSchema']): Overlap | undefined {
  const gameDay = toWeekday(wire.game.day);
  if (gameDay === undefined) return undefined;
  return {
    grade: wire.grade,
    cells: wire.cells.map(toCell).filter((cell): cell is OverlapCell => cell !== undefined),
    game: { day: gameDay, range: wire.game.range },
  };
}

/** The forecast, or nothing where the server could not read one. */
export function toForecast(wire: Schemas['DeckForecastSchema'] | null): Pick<DeckCard, 'forecast'> {
  return wire === null ? {} : { forecast: { pct: wire.pct, provisional: wire.provisional } };
}

/**
 * One card — or nothing, for a card whose game cell names no weekday: the ring would have
 * nowhere to go, and a card drawn without its game's own cell says less than the read did.
 */
export function toDeckCard(wire: Schemas['DeckCardSchema']): DeckCard | undefined {
  const overlap = toOverlap(wire.overlap);
  if (overlap === undefined) return undefined;

  return {
    proposalId: wire.proposal_id,
    type: wire.type,
    kind: KIND_BY_WIRE[wire.kind],
    ...toChallenger(wire.challenger),
    startsAt: wire.starts_at,
    club: toClub(wire.club),
    shareGrosze: wire.share_grosze,
    deadline: wire.deadline,
    inCount: wire.in_count,
    versionCount: wire.version_count,
    openSeatsAfterYourYes: wire.open_seats_after_your_yes,
    court: wire.court,
    ...(wire.court_name === null ? {} : { courtName: wire.court_name }),
    noFreeCancellation: wire.no_free_cancellation,
    clubConfirms: wire.club_confirms,
    sides: toDeckSides(wire.sides),
    ...toForecast(wire.forecast),
    overlap,
  };
}

function toSegment(wire: Schemas['DeckSegmentSchema']): DeckSegment {
  return { kind: KIND_BY_WIRE[wire.kind], count: wire.count };
}

function toCappedWeek(wire: Schemas['CappedWeekSchema']): CappedWeek {
  return { startsOn: wire.starts_on, booked: wire.booked };
}

export function toGroupDeck(wire: Schemas['GroupDeckResponse']): GroupDeck {
  return {
    segments: wire.segments.map(toSegment),
    gamesBadge: wire.games_badge,
    gamesPerWeek: wire.games_per_week,
    cappedWeeks: wire.capped_weeks.map(toCappedWeek),
    cards: wire.cards.map(toDeckCard).filter((card): card is DeckCard => card !== undefined),
  };
}
