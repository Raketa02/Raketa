/**
 * **The ranking, from the wire** ([#775](https://github.com/Raketa02/Raketa/issues/775)) —
 * `GET /rankings/{sport}`'s answer folded into the page's own shapes.
 *
 * **A `null` is an absence here, never a nought**: a win count the server leaves out is a line with
 * no count, a player below who is not there is no second part. And what this build cannot read is
 * drawn as nothing rather than guessed — a card in a state it has never heard of, a place sent
 * without its number, a chip moving up with no count — because each of those would otherwise be a
 * sentence about the reader that the server never said.
 */

import type { components } from '@/generated/schema';

import type {
  Chip,
  GapLine,
  GeneralPage,
  PlaceCard,
  Placed,
  PlayerAbove,
  PlayerBelow,
  RankedRow,
  Ranking,
} from '../domain/ranking';

type Schemas = components['schemas'];

export function toRanking(wire: Schemas['RankingResponse']): Ranking {
  const card = toPlaceCard(wire.card);
  return {
    view: wire.view,
    ...(card === undefined ? {} : { card }),
    listed: wire.listed,
    podium: wire.podium.map(toRankedRow),
    rows: wire.rows.map(toRankedRow),
    ...(wire.next === null ? {} : { next: wire.next }),
  };
}

/** **A page of General** (#776): its rows, and each cursor only where that end has more. */
export function toGeneralPage(wire: Schemas['GeneralPageResponse']): GeneralPage {
  return {
    rows: wire.rows.map(toRankedRow),
    ...(wire.previous === null ? {} : { previous: wire.previous }),
    ...(wire.next === null ? {} : { next: wire.next }),
  };
}

function toPlaceCard(wire: Schemas['PlaceCardSchema']): PlaceCard | undefined {
  switch (wire.state) {
    case 'LISTED': {
      const placed = toPlaced(wire);
      return placed === undefined
        ? undefined
        : { state: 'LISTED', ...placed, gapLine: toGapLine(wire.gap_line) };
    }
    case 'NEEDS_RESULTS':
      return {
        state: 'NEEDS_RESULTS',
        results: wire.results,
        resultsToEnter: wire.results_to_enter,
      };
    case 'NO_LEVEL':
      return { state: 'NO_LEVEL', resultsToEnter: wire.results_to_enter };
    case 'OFF_THE_LIST':
    case 'JUST_YOU':
    case 'NO_FRIEND_LISTED':
      return { state: wire.state };
    default:
      // A state newer than this build: the contract check fails at compile time, and an old phone
      // reading a new server draws no card.
      return undefined;
  }
}

/** The place, *of N* and the level — all three, or none to draw. The chip only where readable. */
function toPlaced(wire: Schemas['PlaceCardSchema']): Placed | undefined {
  if (wire.place === null || wire.of === null || wire.level === null) return undefined;
  const chip = wire.chip === null ? undefined : toChip(wire.chip);
  return {
    place: wire.place,
    of: wire.of,
    level: wire.level,
    ...(chip === undefined ? {} : { chip }),
  };
}

/** First place is the whole line; otherwise the two parts, each only where there is somebody. */
function toGapLine(wire: Schemas['GapLineSchema'] | null): GapLine {
  if (wire?.top_of_the_list === true) return { kind: 'top' };
  return {
    kind: 'between',
    ...(wire?.above == null ? {} : { above: toAbove(wire.above) }),
    ...(wire?.below == null ? {} : { below: toBelow(wire.below) }),
  };
}

function toAbove(wire: Schemas['PlayerAboveSchema']): PlayerAbove {
  return {
    nickname: wire.nickname,
    gap: wire.gap,
    ...(wire.wins === null ? {} : { wins: wire.wins }),
    tied: wire.tied,
  };
}

function toBelow(wire: Schemas['PlayerBelowSchema']): PlayerBelow {
  return { nickname: wire.nickname, gap: wire.gap };
}

function toChip(wire: Schemas['ChipSchema']): Chip | undefined {
  switch (wire.kind) {
    case 'UP':
    case 'DOWN':
      return wire.places === null ? undefined : { kind: wire.kind, places: wire.places };
    case 'SAME':
    case 'NEW':
      return { kind: wire.kind };
    default:
      return undefined;
  }
}

function toRankedRow(wire: Schemas['RankedRowSchema']): RankedRow {
  const chip = toChip(wire.chip);
  return {
    place: wire.place,
    playerId: wire.player_id,
    nickname: wire.nickname,
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    form: wire.form,
    ...(chip === undefined ? {} : { chip }),
    level: wire.level,
    isYou: wire.is_you,
  };
}
