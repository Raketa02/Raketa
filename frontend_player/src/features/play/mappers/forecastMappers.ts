/**
 * The builder's wire boundary: **the two asks it sends, and the court that comes back.**
 *
 * ## Two routes, one shape out of them
 *
 * `POST /lineups` mints a search and answers with a whole ranked list plus a court;
 * `POST /forecasts` mints nothing and answers with three arrangements and two version stamps.
 * They are different requests with different consequences, and the one thing they have in
 * common is the thing the screen draws: **every way round, each with its own forecast.** So
 * `toArrangements` is shared and everything else is not.
 *
 * ## The narrowings, and what each unknown code costs
 *
 * | | |
 * | --- | --- |
 * | a **relationship** | the seat is **dropped** — a seat this build cannot place is not a seat it may draw at a guess |
 * | an **unfilled reason** | the reason is **dropped** and the seat stands: an open seat with nothing to say is a state a forecast's own seats are already in |
 * | a **group reason** | dropped — one sentence over a court, and no total counts it |
 * | a **forecast assumption** | dropped to `null`, and `provisional` still says the figure has a caveat this build cannot state |
 *
 * The seat is the only one that is a drop rather than a gap-in-place, and it is worth being
 * explicit about why: the numbers on a why-fit row are a **column that must sum**, so a row
 * dropped there reappears as an adjustment nobody made. A court is not a total. A seat this
 * build cannot describe would be drawn in the wrong half — which is the one thing `SELF` and
 * `PARTNER` exist to stop a client guessing at — and drawing nothing there is visible, where
 * drawing it wrongly is not.
 *
 * ## No arithmetic crosses here
 *
 * Every number is renamed and none is computed: `pct`, `sigma_group`, the two side strengths,
 * the gap between them and the seat indices all arrive as they were served. That is
 * `the-play-screens.md` §11.3 read at the one layer where a client would be tempted, and the
 * check is *looking for arithmetic*.
 *
 * **The split is the case that makes the rule visible.** `gap` is `your_side − their_side` and
 * the engine sends all three, so this file is one subtraction away from being the place the
 * card's numbers stop agreeing with each other — and it does not make it
 * ([#289](https://github.com/Raketa02/Raketa/issues/289)).
 */

import type { components } from '@/generated/schema';
import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';
import type { WeeklyHour } from '@/shared/vocabulary/week';

import type { Candidate, SearchEnvelope } from '../domain/candidate';
import type {
  Arrangement,
  ArrangementSeat,
  Forecast,
  SeatedCourt,
  SeatedSeat,
  Split,
} from '../domain/forecast';
import type { SeatedPlayerId } from '../domain/lineup';
import {
  FORECAST_ASSUMPTIONS,
  GROUP_REASONS,
  RELATIONSHIPS,
  UNFILLED_REASONS,
  type ForecastAssumption,
  type GroupReason,
  type Relationship,
  type SearchMode,
  type UnfilledReason,
} from '../domain/vocabulary';

import { toRankedList } from './candidateMappers';
import { availabilityOverride } from './searchMappers';

type RunLineupRequest = components['schemas']['RunLineupRequest'];
type LineupResponse = components['schemas']['LineupResponse'];
type ForecastRequest = components['schemas']['ForecastRequest'];
type ForecastResponse = components['schemas']['ForecastResponse'];
type WireArrangement = components['schemas']['ArrangementSchema'];
type WireArrangementSeat = components['schemas']['ArrangementSeatSchema'];
type WireLineupSeat = components['schemas']['LineupSeatSchema'];
type WireForecast = components['schemas']['ForecastSchema'];
type WireSplit = components['schemas']['SplitSchema'];

/**
 * ⚡ *Fill the seats* — **the line-up and fill-seats are one request.**
 *
 * They differ by `locked_seats` being non-empty, *"which is a property of what you send rather
 * than of where you send it"* — so hand-seating somebody and pressing ⚡ is this same shape,
 * and there is no second route for a client to get wrong.
 *
 * There is **no seat count** and there never will be: how many people sit down is the sport's
 * own fact. There is no radius either, for the reason the shortlist has none.
 *
 * `availability_override` is **omitted, never sent as `null`**, and the caller states which it
 * is sending — the same decision `SearchAsk` makes, for #247's reason: an omitted override is
 * *use my profile grid* and an empty list is *I unticked every cell*.
 *
 * **And a fill names the challenge it completes and says nothing else about the court**
 * ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
 * §2). That is a second shape of one request rather than a second route — the same reading
 * `locked_seats` already gets, *"a property of what you send rather than of where you send
 * it"* — so it is a union here, and the three fields the route refuses beside it are unspellable
 * rather than optional.
 */
export type LineupAsk = {
  /** The improvised week, or `undefined` to fill against the grid the profile holds. */
  readonly sentWeek: readonly WeeklyHour[] | undefined;
} & (
  | {
      readonly sport: Sport;
      readonly mode: SearchMode;
      /** The people already on the court, **in seat order**. Empty is ⚡ on an empty court. */
      readonly lockedSeats: readonly SeatedPlayerId[];
      readonly completing?: undefined;
    }
  | {
      /**
       * The half-built court this fill completes — and **the whole of what it says about the
       * court** (ADR-0150 §2).
       *
       * A union rather than three optional fields beside it, because the request refuses the
       * other three here rather than making them optional: *a caller supplying one is offering a
       * second place for a fact the challenge already holds, which is how somebody who is not in
       * the challenge gets locked, or somebody who is gets forgotten.* Spelled as a union, that
       * is a compile error rather than a `400`.
       */
      readonly completing: string;
    }
);

export function toRunLineupRequest(ask: LineupAsk): RunLineupRequest {
  // **Send the challenge and send nothing else about the court.** The sport, the kind of
  // evening and the locked seats are all read off it server-side; `availability_override`
  // stays sendable, because it is *this search's* week and says nothing about the challenge.
  if (ask.completing !== undefined) {
    return { completing_challenge_id: ask.completing, ...availabilityOverride(ask.sentWeek) };
  }

  return {
    sport: toWireSport(ask.sport),
    mode: ask.mode,
    // Omitted rather than sent empty: *send none and the engine fills every seat* is what an
    // absent list means, and an empty array would be the same claim spelled a second way.
    ...(ask.lockedSeats.length === 0 ? {} : { locked_seats: [...ask.lockedSeats] }),
    // The week's own rule is `searchMappers`', because three routes carry it and #247's
    // distinction has to be drawn identically on all three.
    ...availabilityOverride(ask.sentWeek),
  };
}

/**
 * What a four you composed yourself would leave on court.
 *
 * `search_id` is the **Origin key** and is required: *"a forecast about somebody no search of
 * yours showed is refused, not computed."* `players` is the people beside you **in seat
 * order**, one to three, and a seat may be empty — which is the absence of an entry rather
 * than a hole in the list.
 */
export interface ForecastAsk {
  readonly sport: Sport;
  readonly mode: SearchMode;
  readonly searchId: string;
  readonly players: readonly SeatedPlayerId[];
}

export function toForecastRequest(ask: ForecastAsk): ForecastRequest {
  return {
    sport: toWireSport(ask.sport),
    mode: ask.mode,
    search_id: ask.searchId,
    players: [...ask.players],
  };
}

/** One line-up answer: the record's own rows, and the court they were seated on. */
export interface LineupAnswer {
  readonly envelope: SearchEnvelope;
  readonly candidates: readonly Candidate[];
  readonly court: SeatedCourt;
}

export function toLineupAnswer(response: LineupResponse): LineupAnswer {
  // The rows come off the record exactly as a shortlist's do — *"a client that renders a
  // shortlist row can render this one without a branch"* — so the list crosses through the
  // one mapper that already knows how, and this file adds only the court.
  const { envelope, candidates } = toRankedList(response);

  return {
    envelope,
    candidates,
    court: {
      seats: response.lineup.seats.flatMap((seat) => toSeatedSeat(seat) ?? []),
      arrangements: toArrangements(response.lineup.arrangements),
      groupReason: toGroupReason(response.lineup.group_reason) ?? null,
      dock: toUnfilledReason(response.lineup.dock) ?? null,
    },
  };
}

/** Three ways round a four you composed. **No `search_id`** — nothing was searched. */
export function toForecastArrangements(response: ForecastResponse): readonly Arrangement[] {
  return toArrangements(response.arrangements);
}

export function toArrangements(arrangements: readonly WireArrangement[]): readonly Arrangement[] {
  return arrangements.map((one) => ({
    pairingId: one.pairing_id,
    isCurrent: one.is_current,
    // Omitted stays omitted: *there was nothing to be best by here* is a different statement
    // from *this one is not the best*, and a `?? false` would collapse them.
    ...(one.is_best === undefined ? {} : { isBest: one.is_best }),
    isEvenest: one.is_evenest,
    seats: [...one.sides.A, ...one.sides.B].flatMap((seat) => toArrangementSeat(seat) ?? []),
    forecast: toForecast(one.forecast),
    split: toSplit(one.split),
  }));
}

function toArrangementSeat(seat: WireArrangementSeat): ArrangementSeat | undefined {
  const relationship = toRelationship(seat.relationship);
  if (relationship === undefined) return undefined;
  return {
    seatIndex: seat.seat_index,
    relationship,
    ...(seat.player_id === undefined ? {} : { playerId: seat.player_id }),
  };
}

function toSeatedSeat(seat: WireLineupSeat): SeatedSeat | undefined {
  const relationship = toRelationship(seat.relationship);
  if (relationship === undefined) return undefined;
  return {
    seatIndex: seat.seat_index,
    relationship,
    ...(seat.player_id === undefined ? {} : { playerId: seat.player_id }),
    unfilled: toUnfilledReason(seat.unfilled_reason) ?? null,
  };
}

/**
 * The figure and its caveat, **as one object** — never a `pct` beside a boolean.
 *
 * `assumption` is an open string on the wire rather than a union, so it is narrowed here like
 * every other code; `provisional` is passed straight through and never re-derived from it,
 * which is the same rule the renderer on the other side obeys for the same reason.
 */
function toForecast(forecast: WireForecast): Forecast {
  return {
    pct: forecast.pct,
    sigmaGroup: forecast.sigma_group,
    provisional: forecast.provisional,
    assumption: forecast.assumption === null ? null : (toAssumption(forecast.assumption) ?? null),
  };
}

/** Three renames, and **not a subtraction**: the engine's `gap` is the one the card prints. */
function toSplit(split: WireSplit): Split {
  return { yourSide: split.your_side, theirSide: split.their_side, gap: split.gap };
}

const KNOWN_RELATIONSHIPS = new Set<string>(RELATIONSHIPS);
const KNOWN_UNFILLED = new Set<string>(UNFILLED_REASONS);
const KNOWN_GROUP_REASONS = new Set<string>(GROUP_REASONS);
const KNOWN_ASSUMPTIONS = new Set<string>(FORECAST_ASSUMPTIONS);

function toRelationship(relationship: string): Relationship | undefined {
  return KNOWN_RELATIONSHIPS.has(relationship) ? (relationship as Relationship) : undefined;
}

function toUnfilledReason(reason: string | undefined): UnfilledReason | undefined {
  if (reason === undefined) return undefined;
  return KNOWN_UNFILLED.has(reason) ? (reason as UnfilledReason) : undefined;
}

function toGroupReason(reason: string | undefined): GroupReason | undefined {
  if (reason === undefined) return undefined;
  return KNOWN_GROUP_REASONS.has(reason) ? (reason as GroupReason) : undefined;
}

function toAssumption(assumption: string): ForecastAssumption | undefined {
  return KNOWN_ASSUMPTIONS.has(assumption) ? (assumption as ForecastAssumption) : undefined;
}
