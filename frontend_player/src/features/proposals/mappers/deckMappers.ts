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

function toPerson(wire: Schemas['DeckTileSchema']): DeckPerson {
  return {
    playerId: wire.player_id,
    isYou: wire.is_you,
    isIn: wire.is_in,
    ...(wire.name === null ? {} : { name: wire.name }),
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    ...(wire.level === null ? {} : { level: wire.level }),
  };
}

function toCell(wire: Schemas['OverlapCellSchema']): OverlapCell | undefined {
  const day = toWeekday(wire.day);
  return day === undefined ? undefined : { day, range: wire.range, shade: wire.shade };
}

/**
 * One card — or nothing, for a card whose game cell names no weekday: the ring would have
 * nowhere to go, and a card drawn without its game's own cell says less than the read did.
 */
export function toDeckCard(wire: Schemas['DeckCardSchema']): DeckCard | undefined {
  const gameDay = toWeekday(wire.overlap.game.day);
  if (gameDay === undefined) return undefined;

  return {
    proposalId: wire.proposal_id,
    type: wire.type,
    kind: KIND_BY_WIRE[wire.kind],
    ...(wire.challenger === null
      ? {}
      : {
          challenger: {
            playerId: wire.challenger.player_id,
            ...(wire.challenger.name === null ? {} : { name: wire.challenger.name }),
          },
        }),
    startsAt: wire.starts_at,
    club: toClub(wire.club),
    shareGrosze: wire.share_grosze,
    deadline: wire.deadline,
    inCount: wire.in_count,
    versionCount: wire.version_count,
    openSeatsAfterYourYes: wire.open_seats_after_your_yes,
    court: wire.court,
    noFreeCancellation: wire.no_free_cancellation,
    clubConfirms: wire.club_confirms,
    sides: { yours: wire.sides.yours.map(toPerson), theirs: wire.sides.theirs.map(toPerson) },
    ...(wire.forecast === null
      ? {}
      : { forecast: { pct: wire.forecast.pct, provisional: wire.forecast.provisional } }),
    overlap: {
      grade: wire.overlap.grade,
      cells: wire.overlap.cells
        .map(toCell)
        .filter((cell): cell is OverlapCell => cell !== undefined),
      game: { day: gameDay, range: wire.overlap.game.range },
    },
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
