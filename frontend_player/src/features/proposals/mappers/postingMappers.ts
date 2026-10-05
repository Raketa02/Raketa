/**
 * **Posting a game, off the wire and onto it** — `GET /pools/{id}/posting-grid`, its slot, and
 * `POST /pools/{id}/posts` (#546), read into the domain's shape and asked in the wire's
 * ([#558](https://github.com/Raketa02/Raketa/issues/558)).
 *
 * The deck's narrowings, the same ones: a `null` becomes an absent field; the kind is the switch's
 * spelling; a rescue in a sport this build cannot name is dropped, as a *Seats to fill* row is.
 * The grid's week is held to its two values — the route answers nothing else.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';

import type {
  FreeCourt,
  Posted,
  PostingAsk,
  PostingCell,
  PostingGrid,
  PostingSlot,
  PostStillFilling,
  SlotFit,
} from '../domain/posting';
import type { SeatToFill } from '../domain/fillIn';

import { toChallenger, toClub, toKind, toPerson, toWireKind } from './deckMappers';
import { toSeatToFill } from './fillInMappers';

type Schemas = components['schemas'];

/**
 * **The controls' ask, as the three routes take it** — the post's body without its court hour: the
 * generated request, derived rather than restated, so it is `api/`'s `PostingQuery` by construction.
 */
export type WireAsk = Omit<Schemas['PostRequest'], 'club_id' | 'starts_at'>;

export function toWireAsk(ask: PostingAsk): WireAsk {
  return {
    sport: toWireSport(ask.sport),
    kind: toWireKind(ask.kind),
    who: ask.who,
    ...(ask.levelLow === undefined ? {} : { level_low: ask.levelLow }),
    ...(ask.levelHigh === undefined ? {} : { level_high: ask.levelHigh }),
  };
}

function toCell(day: string, wire: Schemas['PostingCellSchema']): PostingCell {
  return {
    day,
    range: wire.range,
    fitsFree: wire.fits_free,
    ...(wire.best_starts_at === null ? {} : { bestStartsAt: wire.best_starts_at }),
    courtFree: wire.court_free,
    fullGame: wire.full_game,
    outsideYourHours: wire.outside_your_hours,
    past: wire.past,
    happening: wire.happening,
  };
}

export function toPostingGrid(wire: Schemas['PostingGridResponse']): PostingGrid {
  return {
    week: wire.week === 2 ? 2 : 1,
    readAt: wire.read_at,
    levelRange: { low: wire.level_range.low, high: wire.level_range.high },
    engineLevelRange: { low: wire.engine_level_range.low, high: wire.engine_level_range.high },
    openSeats: wire.open_seats,
    days: wire.days.map((day) => ({
      day: day.day,
      isToday: day.is_today,
      cells: day.cells.map((cell) => toCell(day.day, cell)),
    })),
  };
}

function toFit(wire: Schemas['SlotFitSchema']): SlotFit {
  return {
    playerId: wire.player_id,
    ...(wire.name === null ? {} : { name: wire.name }),
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    ...(wire.level === null ? {} : { level: wire.level }),
    ...(wire.forecast === null ? {} : { forecastPct: wire.forecast.pct }),
  };
}

function toFreeCourt(wire: Schemas['FreeCourtSchema']): FreeCourt {
  return {
    club: toClub(wire.club),
    homeClub: wire.home_club,
    ...(wire.distance_km === null ? {} : { distanceKm: wire.distance_km }),
    startsAt: wire.starts_at,
    shareGrosze: wire.share_grosze,
    bookBy: wire.book_by,
    courts: wire.courts,
    fitsFree: wire.fits_free,
  };
}

function toPost(wire: Schemas['PostStillFillingSchema']): PostStillFilling {
  return {
    proposalId: wire.proposal_id,
    kind: toKind(wire.kind),
    startsAt: wire.starts_at,
    club: toClub(wire.club),
    shareGrosze: wire.share_grosze,
    bookBy: wire.book_by,
    ...toChallenger(wire.challenger),
    peopleIn: wire.people_in.map(toPerson),
    openSeats: wire.open_seats,
  };
}

export function toPostingSlot(wire: Schemas['PostingSlotResponse']): PostingSlot {
  return {
    day: wire.day,
    range: wire.range,
    readAt: wire.read_at,
    openSeats: wire.open_seats,
    cell: toCell(wire.day, wire.cell),
    fits: wire.fits.map(toFit),
    freeCourts: wire.free_courts.map(toFreeCourt),
    rescues: wire.rescues.map(toSeatToFill).filter((row): row is SeatToFill => row !== undefined),
    posts: wire.posts.map(toPost),
  };
}

export function toPosted(wire: Schemas['PostedResponse']): Posted {
  return {
    proposalId: wire.proposal_id,
    versions: wire.versions,
    dealtTo: wire.dealt_to,
    openSeats: wire.open_seats,
  };
}
