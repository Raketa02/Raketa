/**
 * **One club's Raketa offer, as the backend would keep it** (#535, #670): its courts and their
 * Raketa hours, its exceptions, its prices and its settings, and the setup checklist read off all
 * of them. The rules are the club surface's own, from `backend/openapi.club.json`,
 * kept just deep enough that a test can add a court, paint its week, price its sport and confirm
 * the settings without programming each reply. A test that is about one reply overrides that
 * handler with `stub.on`.
 */

import { randomUUID } from 'node:crypto';

import type { components } from '../../src/generated/schema';

import { STRIPE_PAGES } from '../suite';

import { refusal, type Reply, type StubBackend } from './backend';
import { clubTime, dayFromToday } from './clock';

type Sport = components['schemas']['Sport'];
type PaymentsStatus = components['schemas']['PaymentsStatus'];
type StepState = components['schemas']['StepState'];
type SetupStep = components['schemas']['SetupStep'];
type BandDays = components['schemas']['BandDays'];
export type Court = components['schemas']['CourtResponse'];
export type Exception = components['schemas']['ExceptionResponse'];
type Settings = components['schemas']['RaketaSettingsResponse'];
type SportPrice = components['schemas']['SportPriceResponse'];
type ErrorBody = components['schemas']['ErrorResponse'];

/** How many players a game of each sport seats: the registry's number, never the club's. */
export const SEATS: Readonly<Record<Sport, number>> = {
  PADEL: 4,
  TENNIS: 2,
  SQUASH: 2,
  BADMINTON: 4,
};

const SPORT_ORDER: readonly Sport[] = ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'];

/** A price, in grosze, is 10 zł to 1 000 zł. */
const LEAST_GROSZE = 10_00;
const MOST_GROSZE = 1000_00;

/** Each setting's range, as `setting_out_of_range` names it. */
const BOUNDS = {
  release_lead_days: [1, 13],
  cut_off_hours: [0, 72],
  other_clubs_courts: [1, 50],
} as const;

export const DEFAULT_SETTINGS: Settings = {
  release_lead_days: 3,
  cut_off_hours: 24,
  // On by default, within 10 km, since Q128 (ADR-0202 §7).
  other_clubs_courts: { offered: true, within_km: 10 },
  paused: false,
};

/** **A court of the club**, offered and with no hours unless the test says otherwise. */
export function court(fields: Pick<Court, 'name' | 'sport'> & Partial<Court>): Court {
  return { id: randomUUID(), indoor: true, offered: true, hours: [], ...fields };
}

/** Every hour from `from` until `until` on each of `days`: *Monday to Friday, 17:00–22:00*. */
export function week(days: readonly number[], from: number, until: number): Court['hours'] {
  return days.flatMap((day) =>
    Array.from({ length: until - from }, (_, index) => ({ day, hour: from + index })),
  );
}

/** A booking that holds a court until it is played: none is deleted or given another sport. */
export interface BookingAhead {
  readonly booking_id: string;
  readonly court_id: string;
  /** The hour it begins, as the wire writes an instant. */
  readonly starts_at: string;
}

function tidy(text: string): string {
  return text.trim().replace(/\s+/g, ' ');
}

function bad(code: string, field?: string, more?: Record<string, string | number>) {
  return { status: 400, body: refusal(code, field, more) } as const;
}

function conflict(code: string, field?: string, more?: Record<string, string | number>) {
  return { status: 409, body: refusal(code, field, more) } as const;
}

const hourKey = (hour: { day: number; hour: number }) => hour.day * 100 + hour.hour;

export class FakeClubCourts {
  courts: Court[] = [];
  exceptions: Exception[] = [];
  /** Each priced sport's price and bands, as the desk saved them. */
  prices = new Map<Sport, { price: number; bands: SportPrice['bands'] }>();
  settings: Settings = structuredClone(DEFAULT_SETTINGS);
  /** Whether the club has confirmed its settings: the checklist's last step. */
  confirmed = false;
  payments: PaymentsStatus = 'NOT_STARTED';
  /** Every link to Stripe's pages handed out, oldest first: each works once, as Stripe's do. */
  readonly links: string[] = [];

  constructor(
    private readonly stub: StubBackend,
    /** `null` when the request carries a live access token; the 401 to send otherwise. */
    private readonly guard: (authorization: string | undefined) => {
      status: 401;
      body: ErrorBody;
    } | null,
    /** The sports the club offers now. */
    private readonly sports: () => readonly Sport[],
    /** The club's bookings still to be played (`club.bookings`). */
    private readonly bookingsAhead: () => readonly BookingAhead[],
  ) {}

  /** Price `sport` at `zloty` a court-hour, with no bands. */
  price(sport: Sport, zloty: number): void {
    this.prices.set(sport, { price: zloty * 100, bands: [] });
  }

  /** Everything the checklist needs but payments, done; payments ready makes the club live. */
  ready(payments: PaymentsStatus = 'READY'): void {
    this.payments = payments;
    this.confirmed = true;
    if (!this.courts.some((each) => each.offered)) {
      this.courts.push(court({ name: 'Court 1', sport: 'PADEL', hours: week([1, 2, 3], 17, 21) }));
    }
    for (const each of this.courts) if (!this.prices.has(each.sport)) this.price(each.sport, 120);
  }

  private hasBookingAhead(id: string): boolean {
    return this.bookingsAhead().some((booking) => booking.court_id === id);
  }

  /**
   * The setup checklist, read off everything set, as the backend reads it (#535, #537, #670):
   * the settings wait for nothing.
   */
  setup(): components['schemas']['SetupResponse'] {
    const offered = this.courts.some((each) => each.offered);
    const selling = this.courts.filter((each) => each.offered && each.hours.length > 0);
    const hoursAndPrices =
      selling.length > 0 && selling.every((each) => this.prices.has(each.sport));
    const doneOr = (done: boolean): StepState => (done ? 'DONE' : 'TO_DO');
    const steps: { step: SetupStep; state: StepState }[] = [
      { step: 'CONNECT_PAYMENTS', state: doneOr(this.payments === 'READY') },
      { step: 'COURTS', state: doneOr(offered) },
      { step: 'HOURS_AND_PRICES', state: offered ? doneOr(hoursAndPrices) : 'LOCKED' },
      { step: 'SETTINGS', state: doneOr(this.confirmed) },
    ];
    return {
      steps,
      payments: this.payments,
      live: steps.every((each) => each.state === 'DONE'),
    };
  }

  private settingsResponse(): Settings {
    return structuredClone(this.settings);
  }

  private pricesResponse(): components['schemas']['PricesResponse'] {
    return {
      prices: SPORT_ORDER.filter((sport) => this.sports().includes(sport)).map((sport) => {
        const priced = this.prices.get(sport);
        const seats = SEATS[sport];
        return {
          sport,
          seats,
          price_grosze: priced?.price ?? null,
          share_grosze: priced === undefined ? null : priced.price / seats,
          bands: priced?.bands ?? [],
        };
      }),
    };
  }

  /** The court's name, checked as the backend checks it: a refusal, or the tidied name. */
  private nameOf(raw: string, except?: string) {
    const name = tidy(raw);
    const length = [...name].length;
    if (length < 1 || length > 40) return bad('court_name_invalid', 'name');
    const taken = this.courts.some(
      (each) => each.id !== except && each.name.toLowerCase() === name.toLowerCase(),
    );
    return taken ? conflict('court_name_taken', 'name') : name;
  }

  install(): this {
    const stub = this.stub;

    stub.on('get', '/api/v1/club/setup', ({ headers }) => {
      return this.guard(headers.authorization) ?? { status: 200, body: this.setup() };
    });

    stub.on('get', '/api/v1/club/courts', ({ headers }) => {
      return this.guard(headers.authorization) ?? { status: 200, body: { courts: this.courts } };
    });

    stub.on('post', '/api/v1/club/courts', ({ headers, body }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const name = this.nameOf(body.name);
      // The backend answers `409 court_name_taken` here too, though the contract declares no
      // 409 for this route: a gap in `openapi.club.json` for a backend session to close.
      if (typeof name !== 'string') return name as Reply<'/api/v1/club/courts', 'post'>;
      if (!this.sports().includes(body.sport)) return bad('court_sport_not_offered', 'sport');
      const added = court({ name, sport: body.sport, indoor: body.indoor });
      this.courts.push(added);
      return { status: 201, body: added };
    });

    stub.on('put', '/api/v1/club/courts/{court_id}', ({ headers, params, body }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const now = this.courts.find((each) => each.id === params.court_id);
      if (now === undefined) return { status: 404, body: refusal('court_not_found') };
      const name = this.nameOf(body.name, now.id);
      if (typeof name !== 'string') return name;
      if (!this.sports().includes(body.sport)) return bad('court_sport_not_offered', 'sport');
      if (body.sport !== now.sport && this.hasBookingAhead(now.id)) {
        return conflict('court_has_bookings');
      }
      const changed = {
        ...now,
        name,
        sport: body.sport,
        indoor: body.indoor,
        offered: body.offered,
      };
      this.courts = this.courts.map((each) => (each.id === now.id ? changed : each));
      return { status: 200, body: changed };
    });

    stub.on('delete', '/api/v1/club/courts/{court_id}', ({ headers, params }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      if (!this.courts.some((each) => each.id === params.court_id)) {
        return { status: 404, body: refusal('court_not_found') };
      }
      if (this.hasBookingAhead(params.court_id ?? '')) return conflict('court_has_bookings');
      this.courts = this.courts.filter((each) => each.id !== params.court_id);
      return { status: 204, body: undefined };
    });

    stub.on('put', '/api/v1/club/raketa-hours', ({ headers, body }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      if (body.court_ids.some((id) => !this.courts.some((each) => each.id === id))) {
        return { status: 404, body: refusal('court_not_found') };
      }
      // One cell once, day first and then hour: the week's one canonical order.
      const byKey = new Map(body.hours.map((hour) => [hourKey(hour), hour]));
      const hours = [...byKey.entries()]
        .sort(([a], [b]) => a - b)
        .map(([, hour]) => ({ day: hour.day, hour: hour.hour }));
      this.courts = this.courts.map((each) =>
        body.court_ids.includes(each.id) ? { ...each, hours } : each,
      );
      return { status: 200, body: { courts: this.courts } };
    });

    stub.on('get', '/api/v1/club/exceptions', ({ headers }) => {
      return (
        this.guard(headers.authorization) ?? {
          status: 200,
          body: { exceptions: this.orderedExceptions() },
        }
      );
    });

    stub.on('post', '/api/v1/club/exceptions', ({ headers, body }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const reason = tidy(body.reason);
      if ([...reason].length < 1 || [...reason].length > 80) {
        return bad('exception_reason_invalid', 'reason');
      }
      const { from_hour: from, until_hour: until } = body;
      const hoursOk =
        (from === null && until === null) ||
        (from !== null && until !== null && from >= 7 && until <= 23 && from < until);
      if (!hoursOk) return bad('exception_hours_invalid', 'hours');
      if (body.last_day < body.first_day) return bad('exception_days_invalid', 'days');
      if (body.last_day < dayFromToday(0)) return bad('exception_in_the_past', 'days');
      if (body.court_ids !== null && body.court_ids.length === 0) {
        return bad('exception_courts_required', 'courts');
      }
      const ids = body.court_ids;
      if (ids?.some((id) => !this.courts.some((each) => each.id === id))) {
        return { status: 404, body: refusal('court_not_found') };
      }
      const held = this.bookingsAhead().find((booking) => {
        const { day, hour } = clubTime(booking.starts_at);
        return (
          (ids === null || ids.includes(booking.court_id)) &&
          day >= body.first_day &&
          day <= body.last_day &&
          (from === null || until === null || (hour >= from && hour < until))
        );
      });
      if (held !== undefined) {
        return conflict('court_booked_then', undefined, {
          court_id: held.court_id,
          booking_id: held.booking_id,
          starts_at: held.starts_at,
        });
      }
      const added: Exception = { id: randomUUID(), ...body, reason };
      this.exceptions.push(added);
      return { status: 201, body: added };
    });

    stub.on('delete', '/api/v1/club/exceptions/{exception_id}', ({ headers, params }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      if (!this.exceptions.some((each) => each.id === params.exception_id)) {
        return { status: 404, body: refusal('exception_not_found') };
      }
      this.exceptions = this.exceptions.filter((each) => each.id !== params.exception_id);
      return { status: 204, body: undefined };
    });

    stub.on('get', '/api/v1/club/prices', ({ headers }) => {
      return this.guard(headers.authorization) ?? { status: 200, body: this.pricesResponse() };
    });

    stub.on('put', '/api/v1/club/prices', ({ headers, body }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const seen = new Set<Sport>();
      for (const row of body.prices) {
        const about = (code: string, more?: Record<string, string | number>) =>
          bad(code, 'prices', { sport: row.sport, ...more });
        if (!this.sports().includes(row.sport)) return about('price_sport_not_offered');
        if (seen.has(row.sport)) return about('price_sport_repeated');
        seen.add(row.sport);
        for (const price of [row.price_grosze, ...row.bands.map((band) => band.price_grosze)]) {
          if (price < LEAST_GROSZE || price > MOST_GROSZE) {
            return about('price_out_of_range', { least: LEAST_GROSZE, most: MOST_GROSZE });
          }
          if (price % SEATS[row.sport] !== 0) {
            return about('price_does_not_split', { seats: SEATS[row.sport] });
          }
        }
        for (const band of row.bands) {
          if (band.from_hour < 7 || band.until_hour > 23 || band.from_hour >= band.until_hour) {
            return about('price_band_hours_invalid');
          }
        }
        const overlap = row.bands.some((band, index) =>
          row.bands.some(
            (other, later) =>
              later > index &&
              other.days === band.days &&
              other.from_hour < band.until_hour &&
              band.from_hour < other.until_hour,
          ),
        );
        if (overlap) return about('price_bands_overlap');
      }
      this.prices = new Map(
        body.prices.map((row) => [
          row.sport,
          {
            price: row.price_grosze,
            bands: [...row.bands]
              .sort((a, b) => dayOrder(a.days) - dayOrder(b.days) || a.from_hour - b.from_hour)
              .map((band) => ({ ...band, share_grosze: band.price_grosze / SEATS[row.sport] })),
          },
        ]),
      );
      return { status: 200, body: this.pricesResponse() };
    });

    stub.on('get', '/api/v1/club/raketa-settings', ({ headers }) => {
      return this.guard(headers.authorization) ?? { status: 200, body: this.settingsResponse() };
    });

    stub.on('put', '/api/v1/club/raketa-settings', ({ headers, body }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const values = {
        release_lead_days: body.release_lead_days,
        cut_off_hours: body.cut_off_hours,
        other_clubs_courts: body.other_clubs_courts.within_km,
      };
      for (const [field, [least, most]] of Object.entries(BOUNDS)) {
        const value = values[field as keyof typeof values];
        if (value < least || value > most) {
          return bad('setting_out_of_range', field, { least, most });
        }
      }
      this.settings = structuredClone(body);
      this.confirmed = true;
      return { status: 200, body: this.settingsResponse() };
    });

    // Payments' route, but the account is the Club courts stream's (#537), as the checklist is.
    // A fresh link every time, for the one account; none once Stripe says it is ready.
    stub.on('post', '/api/v1/club/payments/onboarding-link', ({ headers }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      if (this.payments === 'READY') return conflict('payments_already_connected');
      const url = `${STRIPE_PAGES}/${this.links.length + 1}`;
      this.links.push(url);
      return { status: 200, body: { url } };
    });

    return this;
  }

  /** By first day, then the hour it closes from (a whole day first), then the order added. */
  private orderedExceptions(): Exception[] {
    return this.exceptions
      .map((each, added) => ({ each, added }))
      .sort(
        (a, b) =>
          a.each.first_day.localeCompare(b.each.first_day) ||
          (a.each.from_hour ?? -1) - (b.each.from_hour ?? -1) ||
          a.added - b.added,
      )
      .map(({ each }) => each);
  }
}

function dayOrder(days: BandDays): number {
  return days === 'WEEKDAYS' ? 0 : 1;
}
