/**
 * **Courts & prices, wire to view and back.** The only file in this feature that imports a
 * generated type (ADR-0187 §6); everything else reads the view models it makes.
 */

import type { components } from '@/generated/schema';
import type { Sport } from '@/features/club-details/mappers';

type WireCourt = components['schemas']['CourtResponse'];
type WireCourtBody = components['schemas']['CourtRequest'];
type WireCourtChange = components['schemas']['CourtChangeRequest'];
type WireHoursBody = components['schemas']['RaketaHoursRequest'];
type WireException = components['schemas']['ExceptionResponse'];
type WireExceptionBody = components['schemas']['ExceptionRequest'];
type WirePrice = components['schemas']['SportPriceResponse'];
type WirePricesBody = components['schemas']['PricesRequest'];

/**
 * **The zone a club's days and hours are read in.** The club surface carries no zone, and every
 * club is in Poland: the backend stores UTC and shows Europe/Warsaw (the screens C5).
 */
export const CLUB_ZONE = 'Europe/Warsaw';

/** The first hour a cell starts at, and the hour the last one ends: 07:00 to 23:00. */
export const FIRST_HOUR = 7;
export const END_HOUR = 23;

/** Whole hours of a day, `from` up to `until`, exclusive: 9 and 12 are 09:00–12:00. */
export interface HourSpan {
  readonly from: number;
  readonly until: number;
}

/** One hour of an ordinary week: an ISO weekday (1 is Monday) and the hour its cell starts. */
export interface WeekHour {
  readonly day: number;
  readonly hour: number;
}

/** A court as the table and the grid draw it. */
export interface Court {
  readonly id: string;
  readonly name: string;
  readonly sport: Sport;
  readonly indoor: boolean;
  /** Offered to Raketa, or switched off: kept, with its hours, and selling nothing new. */
  readonly offered: boolean;
  /** Its Raketa hours, Monday first and in the grid's order. Empty until they are painted. */
  readonly hours: readonly WeekHour[];
}

export function toCourt(wire: WireCourt): Court {
  return {
    id: wire.id,
    name: wire.name,
    sport: wire.sport,
    indoor: wire.indoor,
    offered: wire.offered,
    hours: wire.hours.map((cell) => ({ day: cell.day, hour: cell.hour })),
  };
}

/** What *Add a court* sends: the three facts a court is born with. */
export interface CourtFacts {
  readonly name: string;
  readonly sport: Sport;
  readonly indoor: boolean;
}

export function toCourtBody(facts: CourtFacts): WireCourtBody {
  return { name: facts.name, sport: facts.sport, indoor: facts.indoor };
}

/** An edit or a switch sends all four, every time: a full replacement. */
export function toCourtChange(facts: CourtFacts, offered: boolean): WireCourtChange {
  return { ...toCourtBody(facts), offered };
}

export function toHoursBody(
  courtIds: readonly string[],
  hours: readonly WeekHour[],
): WireHoursBody {
  return {
    court_ids: [...courtIds],
    hours: hours.map((cell) => ({ day: cell.day, hour: cell.hour })),
  };
}

/** **An exception**: hours closed without touching the weekly pattern. */
export interface Exception {
  readonly id: string;
  /** `null` for every court, one added later included; otherwise those courts' ids. */
  readonly courtIds: readonly string[] | null;
  /** Local days, `2026-10-12`, the last included. */
  readonly firstDay: string;
  readonly lastDay: string;
  /** The hours it closes on each day, or `null` for the whole day. */
  readonly hours: HourSpan | null;
  readonly reason: string;
}

export function toException(wire: WireException): Exception {
  return {
    id: wire.id,
    courtIds: wire.court_ids,
    firstDay: wire.first_day,
    lastDay: wire.last_day,
    hours:
      wire.from_hour === null || wire.until_hour === null
        ? null
        : { from: wire.from_hour, until: wire.until_hour },
    reason: wire.reason,
  };
}

export function toExceptionBody(exception: Omit<Exception, 'id'>): WireExceptionBody {
  return {
    court_ids: exception.courtIds === null ? null : [...exception.courtIds],
    first_day: exception.firstDay,
    last_day: exception.lastDay,
    from_hour: exception.hours?.from ?? null,
    until_hour: exception.hours?.until ?? null,
    reason: exception.reason,
  };
}

/**
 * **The booking an exception would close**, from a `court_booked_then` refusal: its court, its
 * id, and the local day of its hour, which is where the Bookings page shows it. `null` for any
 * other refusal, or one that names none of them.
 */
export interface BookedThen {
  readonly courtId: string;
  readonly bookingId: string;
  readonly day: string;
}

export function toBookedThen(error: {
  readonly code: string;
  readonly details?: Readonly<Record<string, string>>;
}): BookedThen | null {
  if (error.code !== 'court_booked_then') return null;
  const { court_id: courtId, booking_id: bookingId, starts_at: startsAt } = error.details ?? {};
  if (courtId === undefined || bookingId === undefined || startsAt === undefined) return null;
  const instant = Date.parse(startsAt);
  return Number.isNaN(instant) ? null : { courtId, bookingId, day: clubDay(instant) };
}

/** The local day at the club an instant falls on: `2026-10-12`. */
export function clubDay(instant: number): string {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone: CLUB_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(instant);
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((each) => each.type === type)?.value ?? '';
  return `${part('year')}-${part('month')}-${part('day')}`;
}

/** Weekdays (Monday to Friday) or the weekend (Saturday and Sunday). */
export type BandDays = components['schemas']['BandDays'];

/** A `Record` over the wire's enum, so a third kind of days fails to compile until it is named. */
const KNOWN_BAND_DAYS: Readonly<Record<BandDays, true>> = { WEEKDAYS: true, WEEKEND: true };

export const BAND_DAYS = Object.keys(KNOWN_BAND_DAYS) as readonly BandDays[];

export function isBandDays(value: unknown): value is BandDays {
  return typeof value === 'string' && value in KNOWN_BAND_DAYS;
}

/** **A price band**: some hours of weekdays or the weekend, priced differently. */
export interface Band extends HourSpan {
  readonly days: BandDays;
  readonly priceGrosze: number;
}

/** **What a court-hour of one sport costs**, as the price table holds it. */
export interface SportPrice {
  readonly sport: Sport;
  /** How many players a game of the sport seats: the registry's number, never the club's. */
  readonly seats: number;
  /** The standard price, or `null` while the sport is not priced. */
  readonly priceGrosze: number | null;
  readonly bands: readonly Band[];
}

export function toSportPrice(wire: WirePrice): SportPrice {
  return {
    sport: wire.sport,
    seats: wire.seats,
    priceGrosze: wire.price_grosze,
    bands: wire.bands.map((band) => ({
      days: band.days,
      from: band.from_hour,
      until: band.until_hour,
      priceGrosze: band.price_grosze,
    })),
  };
}

/** The whole table, every time: a sport left out is no longer priced. */
export function toPricesBody(
  prices: readonly {
    readonly sport: Sport;
    readonly priceGrosze: number;
    readonly bands: readonly Band[];
  }[],
): WirePricesBody {
  return {
    prices: prices.map((price) => ({
      sport: price.sport,
      price_grosze: price.priceGrosze,
      bands: price.bands.map((band) => ({
        days: band.days,
        from_hour: band.from,
        until_hour: band.until,
        price_grosze: band.priceGrosze,
      })),
    })),
  };
}

/**
 * The sport a price refusal is about: `details.sport` of any refusal of the table, which names
 * the row (`details.field` is `prices`).
 */
export function refusedSport(error: {
  readonly details?: Readonly<Record<string, string>>;
}): string | null {
  return error.details?.sport ?? null;
}
