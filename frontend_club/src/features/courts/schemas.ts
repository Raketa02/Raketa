/**
 * **Courts & prices as its forms hold them, and the checks a save makes before it leaves.** They
 * restate the backend's rules (ADR-0187's accepted cost of independent apps) and refuse with its
 * codes, keyed by the field its refusal names, so one sentence serves either side. The
 * website's own codes are `court_sport_required` and `court_indoor_required` (a court not yet
 * described), `exception_day_required` (no day chosen), and `price_invalid` and
 * `price_required` (a price that is not one, or bands with no price under them).
 */

import { isSport, type Sport } from '@/features/club-details/mappers';
import { between, tidy } from '@/features/club-details/schemas';
import { parseZloty, zlotyFigure } from '@/ui/format';
import { formIds, formText, type Refusals } from '@/ui/forms';

import {
  END_HOUR,
  FIRST_HOUR,
  isBandDays,
  type Band,
  type BandDays,
  type Court,
  type CourtFacts,
  type Exception,
  type HourSpan,
  type SportPrice,
  type WeekHour,
} from './mappers';

// --- A court -----------------------------------------------------------------

export const COURT_FIELDS = ['name', 'sport', 'indoor'] as const;

export type CourtField = (typeof COURT_FIELDS)[number];

export interface CourtDraft {
  readonly name: string;
  readonly sport: Sport | null;
  /** `null` until the desk says indoor or outdoor. */
  readonly indoor: boolean | null;
}

export const EMPTY_COURT: CourtDraft = { name: '', sport: null, indoor: null };

export function courtDraftOf(court: Court): CourtDraft {
  return { name: court.name, sport: court.sport, indoor: court.indoor };
}

export function readCourt(form: FormData): CourtDraft {
  const sport = formText(form, 'sport');
  const indoor = formText(form, 'indoor');
  return {
    name: formText(form, 'name'),
    sport: isSport(sport) ? sport : null,
    indoor: indoor === 'indoor' ? true : indoor === 'outdoor' ? false : null,
  };
}

export function checkCourt(draft: CourtDraft): Refusals<CourtField> {
  const refusals: Refusals<CourtField> = {};
  if (!between(draft.name, 1, 40)) refusals.name = 'court_name_invalid';
  if (draft.sport === null) refusals.sport = 'court_sport_required';
  if (draft.indoor === null) refusals.indoor = 'court_indoor_required';
  return refusals;
}

/** What the table does to a court: switch it off (once confirmed) or on, or delete it. */
export const COURT_ACTS = ['switch-off', 'switch-on', 'delete'] as const;

export type CourtAct = (typeof COURT_ACTS)[number];

export function isCourtAct(value: string): value is CourtAct {
  return (COURT_ACTS as readonly string[]).includes(value);
}

/** A draft that passed {@link checkCourt}, as the court a save sends. */
export function factsOf(draft: CourtDraft & { sport: Sport; indoor: boolean }): CourtFacts {
  return { name: tidy(draft.name), sport: draft.sport, indoor: draft.indoor };
}

// --- A week ------------------------------------------------------------------

/** One cell of the grid as a form posts it and the grid keys it: `3:19`, Wednesday 19:00. */
export function cellKey(cell: WeekHour): string {
  return `${cell.day}:${cell.hour}`;
}

function cellOf(key: string): WeekHour | null {
  const match = /^([1-7]):(\d{1,2})$/.exec(key);
  if (match === null) return null;
  const hour = Number(match[2]);
  return hour >= FIRST_HOUR && hour < END_HOUR ? { day: Number(match[1]), hour } : null;
}

/** The week's one order, day first and then hour, each cell once: as the backend keeps it. */
export function inWeekOrder(keys: Iterable<string>): WeekHour[] {
  return [...new Set(keys)]
    .map(cellOf)
    .filter((cell): cell is WeekHour => cell !== null)
    .sort((a, b) => a.day - b.day || a.hour - b.hour);
}

/** What *Save hours* posts: the courts to give the week to, and the week. */
export function readHours(form: FormData): { courtIds: string[]; hours: WeekHour[] } {
  return {
    courtIds: formIds(form, 'court'),
    hours: inWeekOrder(
      form.getAll('hour').filter((value): value is string => typeof value === 'string'),
    ),
  };
}

// --- An exception ------------------------------------------------------------

export const EXCEPTION_FIELDS = ['courts', 'days', 'hours', 'reason'] as const;

export type ExceptionField = (typeof EXCEPTION_FIELDS)[number];

/** What an exception closes: every court, or the ones ticked. */
export type WhichCourts = 'all' | 'some';

/** How long it closes: a day, several days, or some hours on a day; one shape at the backend. */
export type ClosedFor = 'day' | 'days' | 'hours';

export interface ExceptionDraft {
  readonly scope: WhichCourts;
  readonly courtIds: readonly string[];
  readonly when: ClosedFor;
  /** As a date box holds it: `2026-10-12`, or `''`. */
  readonly firstDay: string;
  readonly lastDay: string;
  /** As the hour boxes hold them: `9`, or `''`. */
  readonly from: string;
  readonly until: string;
  readonly reason: string;
}

export const EMPTY_EXCEPTION: ExceptionDraft = {
  scope: 'all',
  courtIds: [],
  when: 'day',
  firstDay: '',
  lastDay: '',
  from: '',
  until: '',
  reason: '',
};

export function readException(form: FormData): ExceptionDraft {
  const when = formText(form, 'when');
  const kind: ClosedFor = when === 'days' || when === 'hours' ? when : 'day';
  const firstDay = formText(form, 'first_day');
  return {
    scope: formText(form, 'scope') === 'some' ? 'some' : 'all',
    courtIds: formIds(form, 'court'),
    when: kind,
    firstDay,
    lastDay: kind === 'days' ? formText(form, 'last_day') : firstDay,
    from: kind === 'hours' ? formText(form, 'from') : '',
    until: kind === 'hours' ? formText(form, 'until') : '',
    reason: formText(form, 'reason'),
  };
}

const isDay = (text: string) => /^\d{4}-\d{2}-\d{2}$/.test(text);

/** The hours an exception or a band closes or prices: whole, within the grid, at least one. */
function hoursWithin(from: string, until: string): HourSpan | null {
  if (!/^\d{1,2}$/.test(from) || !/^\d{1,2}$/.test(until)) return null;
  const [start, end] = [Number(from), Number(until)];
  return start >= FIRST_HOUR && end <= END_HOUR && start < end ? { from: start, until: end } : null;
}

/** `today` is the local day at the club, so a day already over there is refused here too. */
export function checkException(draft: ExceptionDraft, today: string): Refusals<ExceptionField> {
  const refusals: Refusals<ExceptionField> = {};
  if (!between(draft.reason, 1, 80)) refusals.reason = 'exception_reason_invalid';
  if (!isDay(draft.firstDay) || !isDay(draft.lastDay)) refusals.days = 'exception_day_required';
  else if (draft.lastDay < draft.firstDay) refusals.days = 'exception_days_invalid';
  else if (draft.lastDay < today) refusals.days = 'exception_in_the_past';
  if (draft.when === 'hours' && hoursWithin(draft.from, draft.until) === null) {
    refusals.hours = 'exception_hours_invalid';
  }
  if (draft.scope === 'some' && draft.courtIds.length === 0) {
    refusals.courts = 'exception_courts_required';
  }
  return refusals;
}

/** A draft that passed {@link checkException}, as the exception a save sends. */
export function exceptionOf(draft: ExceptionDraft): Omit<Exception, 'id'> {
  return {
    courtIds: draft.scope === 'all' ? null : draft.courtIds,
    firstDay: draft.firstDay,
    lastDay: draft.lastDay,
    hours: draft.when === 'hours' ? hoursWithin(draft.from, draft.until) : null,
    reason: tidy(draft.reason),
  };
}

// --- Prices ------------------------------------------------------------------

/** A price, in grosze, is 10 zł to 1 000 zł (#535). */
const LEAST_GROSZE = 10_00;
const MOST_GROSZE = 1000_00;

/**
 * What is wrong with one price, as the backend's code: out of its range, or not splitting into
 * whole grosze among the sport's seats. `null` for a price the backend takes.
 */
function priceFault(grosze: number, seats: number): string | null {
  if (grosze < LEAST_GROSZE || grosze > MOST_GROSZE) return 'price_out_of_range';
  return grosze % seats === 0 ? null : 'price_does_not_split';
}

export interface BandDraft {
  readonly days: BandDays;
  /** As the hour boxes hold them: `17`. */
  readonly from: string;
  readonly until: string;
  /** As typed: `160`, `142,50`. */
  readonly price: string;
}

export interface PriceDraft {
  readonly sport: Sport;
  readonly seats: number;
  /** As typed; `''` with no bands leaves the sport unpriced. */
  readonly price: string;
  readonly bands: readonly BandDraft[];
}

/** A band as *+ Add a price band* starts it: weekday evenings, the price still to type. */
export const NEW_BAND: BandDraft = { days: 'WEEKDAYS', from: '17', until: '22', price: '' };

export function priceDraftOf(price: SportPrice): PriceDraft {
  return {
    sport: price.sport,
    seats: price.seats,
    price: price.priceGrosze === null ? '' : zlotyFigure(price.priceGrosze),
    bands: price.bands.map((band) => ({
      days: band.days,
      from: String(band.from),
      until: String(band.until),
      price: zlotyFigure(band.priceGrosze),
    })),
  };
}

/**
 * The table as *Save prices* posts it: each sport's row by its name (`price-PADEL`), with its
 * seats as the page was given them, and its bands as parallel lists in the order drawn.
 */
export function readPrices(form: FormData): PriceDraft[] {
  const sports = form.getAll('sport').filter(isSport);
  return sports.map((sport) => {
    const all = (name: string) =>
      form.getAll(`${name}-${sport}`).map((value) => (typeof value === 'string' ? value : ''));
    const prices = all('band-price');
    const from = all('band-from');
    const until = all('band-until');
    return {
      sport,
      seats: Number(formText(form, `seats-${sport}`)) || 1,
      price: formText(form, `price-${sport}`),
      bands: all('band-days').map((days, index) => ({
        days: isBandDays(days) ? days : 'WEEKDAYS',
        from: from[index] ?? '',
        until: until[index] ?? '',
        price: prices[index] ?? '',
      })),
    };
  });
}

/** A row the backend would accept: a priced sport, with its bands. */
export interface PriceRow {
  readonly sport: Sport;
  readonly priceGrosze: number;
  readonly bands: readonly Band[];
}

/** One sport's row, checked: nothing priced, the first thing wrong with it, or the row. */
type CheckedRow =
  { readonly unpriced: true } | { readonly refusal: string } | { readonly row: PriceRow };

/** The first thing wrong with one sport's row, as the backend's code or this site's. */
function checkRow(draft: PriceDraft): CheckedRow {
  if (draft.price.trim() === '' && draft.bands.length === 0) return { unpriced: true };
  if (draft.price.trim() === '') return { refusal: 'price_required' };
  const price = parseZloty(draft.price);
  const bandPrices = draft.bands.map((band) => parseZloty(band.price));
  if (price === null || bandPrices.includes(null)) return { refusal: 'price_invalid' };
  const bands: Band[] = [];
  for (const [index, band] of draft.bands.entries()) {
    const hours = hoursWithin(band.from, band.until);
    if (hours === null) return { refusal: 'price_band_hours_invalid' };
    bands.push({ days: band.days, ...hours, priceGrosze: bandPrices[index] ?? 0 });
  }
  const prices = [price, ...bands.map((band) => band.priceGrosze)];
  const fault = prices
    .map((each) => priceFault(each, draft.seats))
    .find((each): each is string => each !== null);
  if (fault !== undefined) return { refusal: fault };
  const overlap = bands.some((band, index) =>
    bands
      .slice(index + 1)
      .some(
        (other) => other.days === band.days && other.from < band.until && band.from < other.until,
      ),
  );
  if (overlap) return { refusal: 'price_bands_overlap' };
  return { row: { sport: draft.sport, priceGrosze: price, bands } };
}

/** Each sport's refusal, or the rows a save sends: every priced sport, the others left out. */
export function checkPrices(drafts: readonly PriceDraft[]): {
  refusals: Refusals<Sport>;
  rows: PriceRow[];
} {
  const refusals: Refusals<Sport> = {};
  const rows: PriceRow[] = [];
  for (const draft of drafts) {
    const checked = checkRow(draft);
    if ('refusal' in checked) refusals[draft.sport] = checked.refusal;
    else if ('row' in checked) rows.push(checked.row);
  }
  return { refusals, rows };
}

/** A typed price the backend would take, in grosze: what the share preview is drawn from. */
export function takenPrice(typed: string, seats: number): number | null {
  const price = parseZloty(typed);
  return price === null || priceFault(price, seats) !== null ? null : price;
}
