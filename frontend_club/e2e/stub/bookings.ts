/**
 * **The club's Raketa bookings, as the backend would keep them** (#543, #547, #626): each booking's
 * court, hour, players and money, and its status **folded on every read** from where it stands
 * and the clock, as `proposals/domain/club_bookings.py` folds it. The rules are the club
 * surface's own, from `backend/openapi.club.json`, kept just deep enough that a test can list a
 * day, answer a request, move a game and cancel one without programming each reply. A test that
 * is about one reply overrides that handler with `stub.on`.
 */

import { randomUUID } from 'node:crypto';

import type { components } from '../../src/generated/schema';

import { refusal, type StubBackend } from './backend';
import { atClubHour, clubTime, dayFromToday } from './clock';
import { SEATS, type Court, type Exception } from './courts';

type ClubStatus = components['schemas']['ClubStatus'];
type ClubFilter = components['schemas']['ClubFilter'];
type ClubBooking = components['schemas']['ClubBookingSchema'];
type CalledOffReason = components['schemas']['CalledOffReason'];
type TimeTo = components['schemas']['TimeTo'];
type ErrorBody = components['schemas']['ErrorResponse'];

const HOUR_MS = 3_600_000;
const MINUTE_MS = 60_000;
/** The club's cut-off unless a test says otherwise: the setting's default, a day before (§16.6). */
const CUT_OFF_MS = 24 * HOUR_MS;

/**
 * Where a booking stands, before the clock is read: waiting for the club's answer, accepted and
 * waiting on one player's payment, booked whole or with a seat open, or called off. *Played*,
 * *no answer* and a payment not in time are read off the clock.
 */
export type Stage =
  'WAITING_FOR_YOU' | 'WAITING_FOR_A_PAYMENT' | 'BOOKED' | 'SEAT_OPEN' | 'CALLED_OFF';

/** **A booking as the fake keeps it**: the wire's row, but where it stands rather than its status. */
export type FakeBooking = Omit<ClubBooking, 'status' | 'ends_at' | 'may_move_or_cancel'> & {
  court_id: string;
  stage: Stage;
  /**
   * The cut-off the game was booked with, which the club's read never sends (§16.6): before it a
   * share is held and a refused card is fixed, after it a share is taken and paid (#637, #638).
   */
  cut_off: string;
  /** What the desk wrote when it refused the request, for its own records. */
  refusal_reason: string | null;
};

/** The names a game's players get unless a test names them, the first side first. */
const NAMES = ['Anna Nowak', 'Piotr Sikora', 'Kasia Wiśniewska', 'Marek Zając'];

/** Before the cut-off a refused card is fixed; after it, the share is paid (#638). */
function timeTo(cutOff: string): TimeTo {
  return Date.now() < Date.parse(cutOff) ? 'FIX_THE_CARD' : 'PAY';
}

/**
 * **A booking on `court` at `hour` of the local `day`**: booked and full, from an official group,
 * with a cut-off a day before it, unless the test says otherwise. A booked game's shares are held
 * while its cut-off is ahead and taken once it has passed, and only a taken share is collected
 * (#637). A waiting request is answered within half an hour and nobody has paid it; an accepted
 * one waits half an hour for one player's card or payment, nobody paid yet; one with a seat open
 * lacks its last player.
 */
export function booking(
  fields: { court: Court; day: string; hour: number; stage?: Stage } & Partial<
    Omit<FakeBooking, 'court_id' | 'court_name' | 'sport' | 'starts_at' | 'stage'>
  >,
): FakeBooking {
  const { court, day, hour, stage = 'BOOKED', ...rest } = fields;
  const seats = SEATS[court.sport];
  const share = 35_00;
  const seated = stage === 'SEAT_OPEN' ? seats - 1 : seats;
  const startsAt = atClubHour(day, hour);
  const cutOff = rest.cut_off ?? new Date(Date.parse(startsAt) - CUT_OFF_MS).toISOString();
  const booked = stage === 'BOOKED' || stage === 'SEAT_OPEN';
  const taken = booked && Date.now() >= Date.parse(cutOff);
  const inHalfAnHour = new Date(Date.now() + 30 * MINUTE_MS).toISOString();
  const players = NAMES.slice(0, seated).map((name) => ({
    player_id: randomUUID(),
    name,
    paid: taken,
    held: booked && !taken,
  }));
  return {
    booking_id: randomUUID(),
    court_id: court.id,
    court_name: court.name,
    sport: court.sport,
    kind: 'COMPETITIVE',
    starts_at: startsAt,
    stage,
    cut_off: cutOff,
    called_off_reason: null,
    cancel_reason: null,
    players,
    open_seats: seats - seated,
    money: {
      price_grosze: share * seats,
      collected_grosze: taken ? share * seated : 0,
      refunded_grosze: 0,
    },
    booked_from: { group_id: randomUUID(), name: 'Ogrody 33 Club', official: true },
    answer_by: stage === 'WAITING_FOR_YOU' ? inHalfAnHour : null,
    payment_due_by: stage === 'WAITING_FOR_A_PAYMENT' ? inHalfAnHour : null,
    time_to: stage === 'WAITING_FOR_A_PAYMENT' ? timeTo(cutOff) : null,
    refusal_reason: null,
    ...rest,
  };
}

/** Each filter, by the status it shows. */
const FILTERED: Readonly<Record<Exclude<ClubFilter, 'ALL'>, ClubStatus>> = {
  WAITING_FOR_YOU: 'WAITING_FOR_YOU',
  SEAT_OPEN: 'SEAT_OPEN',
  CALLED_OFF: 'CALLED_OFF',
};

export class FakeClubBookings {
  /** Every booking at the club, any day; the page lists one day's, soonest first. */
  bookings: FakeBooking[] = [];

  constructor(
    private readonly stub: StubBackend,
    /** `null` when the request carries a live access token; the 401 to send otherwise. */
    private readonly guard: (authorization: string | undefined) => {
      status: 401;
      body: ErrorBody;
    } | null,
    /** The club's courts and exceptions now: where a game may be moved. */
    private readonly offer: () => {
      courts: readonly Court[];
      exceptions: readonly Exception[];
    },
  ) {}

  /** Seat a booking, and answer it, so a test can name it. */
  add(added: FakeBooking): FakeBooking {
    this.bookings.push(added);
    return added;
  }

  /** A booked game on `court` at `hour` of the local `day`: the one an exception may not close. */
  book(court: Court, day: string, hour: number): FakeBooking {
    return this.add(booking({ court, day, hour }));
  }

  find(id: string | undefined): FakeBooking | undefined {
    return this.bookings.find((each) => each.booking_id === id);
  }

  /**
   * **The game's cut-off comes now** (#637): every share held for it is taken, and collected, as
   * the backend's cut-off job takes them. A test calls it where the clock would have passed it.
   */
  passTheCutOff(game: FakeBooking): FakeBooking {
    const share = game.money.price_grosze / SEATS[game.sport];
    const held = game.players.filter((player) => player.held).length;
    return this.replace({
      ...game,
      cut_off: new Date().toISOString(),
      players: game.players.map((player) =>
        player.held ? { ...player, held: false, paid: true } : player,
      ),
      money: { ...game.money, collected_grosze: game.money.collected_grosze + share * held },
    });
  }

  /**
   * Why the game will not be played, now: a request unanswered past its time is *no answer*, and
   * a yes whose payment did not come by its time is *payment not in time*.
   */
  private calledOff(held: FakeBooking): CalledOffReason | null {
    if (held.stage === 'CALLED_OFF') return held.called_off_reason;
    if (held.stage === 'WAITING_FOR_YOU' && held.answer_by !== null) {
      if (Date.now() >= Date.parse(held.answer_by)) return 'NO_ANSWER';
    }
    if (held.stage === 'WAITING_FOR_A_PAYMENT' && held.payment_due_by !== null) {
      if (Date.now() >= Date.parse(held.payment_due_by)) return 'PAYMENT_NOT_IN_TIME';
    }
    return null;
  }

  status(held: FakeBooking): ClubStatus {
    if (this.calledOff(held) !== null) return 'CALLED_OFF';
    if (held.stage === 'WAITING_FOR_YOU') return 'WAITING_FOR_YOU';
    if (held.stage === 'WAITING_FOR_A_PAYMENT') return 'WAITING_FOR_A_PAYMENT';
    if (Date.now() >= Date.parse(held.starts_at) + HOUR_MS) return 'PLAYED';
    return held.stage === 'SEAT_OPEN' ? 'SEAT_OPEN' : 'BOOKED';
  }

  /** Booked, whole or with a seat open, not called off, and its hour still ahead. */
  private stillToBePlayed(held: FakeBooking): boolean {
    return (
      (held.stage === 'BOOKED' || held.stage === 'SEAT_OPEN') &&
      this.calledOff(held) === null &&
      Date.now() < Date.parse(held.starts_at)
    );
  }

  /** Bookings a court is held by until they are played: not called off, the hour not over. */
  ahead(): readonly FakeBooking[] {
    return this.bookings.filter(
      (held) => this.calledOff(held) === null && Date.now() < Date.parse(held.starts_at) + HOUR_MS,
    );
  }

  private row(held: FakeBooking): ClubBooking {
    const status = this.status(held);
    return {
      booking_id: held.booking_id,
      starts_at: held.starts_at,
      ends_at: new Date(Date.parse(held.starts_at) + HOUR_MS).toISOString(),
      court_name: held.court_name,
      sport: held.sport,
      kind: held.kind,
      status,
      called_off_reason: this.calledOff(held),
      cancel_reason: held.cancel_reason,
      players: held.players,
      open_seats: held.open_seats,
      money: held.money,
      booked_from: held.booked_from,
      answer_by: status === 'WAITING_FOR_YOU' ? held.answer_by : null,
      payment_due_by: status === 'WAITING_FOR_A_PAYMENT' ? held.payment_due_by : null,
      time_to: status === 'WAITING_FOR_A_PAYMENT' ? held.time_to : null,
      may_move_or_cancel: this.stillToBePlayed(held),
    };
  }

  /** Every other court of the game's sport the club sells at its hour, in the club's order. */
  freeCourts(held: FakeBooking): Court[] {
    const { courts, exceptions } = this.offer();
    const { day, weekday, hour } = clubTime(held.starts_at);
    const closed = (court: Court) =>
      exceptions.some(
        (each) =>
          (each.court_ids === null || each.court_ids.includes(court.id)) &&
          each.first_day <= day &&
          day <= each.last_day &&
          (each.from_hour === null ||
            each.until_hour === null ||
            (each.from_hour <= hour && hour < each.until_hour)),
      );
    const taken = new Set(
      this.ahead()
        .filter((other) => other.starts_at === held.starts_at)
        .map((other) => other.court_id),
    );
    return courts.filter(
      (court) =>
        court.offered &&
        court.sport === held.sport &&
        !taken.has(court.id) &&
        court.hours.some((cell) => cell.day === weekday && cell.hour === hour) &&
        !closed(court),
    );
  }

  /** Why the club may not move or cancel the game now, or `null` when it may. */
  private stillPlayable(held: FakeBooking) {
    if (this.status(held) === 'WAITING_FOR_YOU') return conflict('booking_not_booked');
    if (this.calledOff(held) !== null) return conflict('booking_is_called_off');
    if (!this.stillToBePlayed(held)) return conflict('game_has_started');
    return null;
  }

  /** Why the club may not answer the request now, or `null` when it may. */
  private stillWaiting(held: FakeBooking) {
    if (held.stage === 'WAITING_FOR_YOU' && this.calledOff(held) === 'NO_ANSWER') {
      this.replace({ ...held, stage: 'CALLED_OFF', called_off_reason: 'NO_ANSWER' });
      return conflict('request_timed_out');
    }
    return held.stage === 'WAITING_FOR_YOU' ? null : conflict('request_not_waiting');
  }

  private replace(changed: FakeBooking): FakeBooking {
    this.bookings = this.bookings.map((each) =>
      each.booking_id === changed.booking_id ? changed : each,
    );
    return changed;
  }

  install(): this {
    const stub = this.stub;
    const notFound = { status: 404, body: refusal('booking_not_found') } as const;

    stub.on('get', '/api/v1/club/bookings', ({ headers, query }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const day = query.date ?? dayFromToday(0);
      const filter = (query.filter ?? 'ALL') as ClubFilter;
      const rows = this.bookings
        .filter((held) => clubTime(held.starts_at).day === day)
        .sort((a, b) => Date.parse(a.starts_at) - Date.parse(b.starts_at))
        .map((held) => this.row(held));
      const count = (status: ClubStatus) => rows.filter((each) => each.status === status).length;
      return {
        status: 200,
        body: {
          day,
          read_at: new Date().toISOString(),
          filter,
          counts: {
            all: rows.length,
            waiting_for_you: count('WAITING_FOR_YOU'),
            seat_open: count('SEAT_OPEN'),
            called_off: count('CALLED_OFF'),
          },
          bookings:
            filter === 'ALL' ? rows : rows.filter((each) => each.status === FILTERED[filter]),
        },
      };
    });

    stub.on('get', '/api/v1/club/bookings/waiting', ({ headers }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const waiting = this.bookings
        .filter((held) => this.status(held) === 'WAITING_FOR_YOU')
        .sort((a, b) => Date.parse(a.answer_by ?? '') - Date.parse(b.answer_by ?? ''));
      return {
        status: 200,
        body: {
          read_at: new Date().toISOString(),
          bookings: waiting.map((held) => ({
            booking_id: held.booking_id,
            sport: held.sport,
            kind: held.kind,
            starts_at: held.starts_at,
            ends_at: new Date(Date.parse(held.starts_at) + HOUR_MS).toISOString(),
            court_name: held.court_name,
            players: held.players.map(({ player_id, name }) => ({ player_id, name })),
            price_grosze: held.money.price_grosze,
            share_grosze: held.money.price_grosze / SEATS[held.sport],
            answer_by: held.answer_by ?? '',
          })),
        },
      };
    });

    stub.on('post', '/api/v1/club/bookings/{booking_id}/acceptance', ({ headers, params }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const held = this.find(params.booking_id);
      if (held === undefined) return notFound;
      const refused = this.stillWaiting(held);
      if (refused !== null) return refused;
      // Every share is held until the cut-off, or taken at once after it (#637).
      const taken = Date.now() >= Date.parse(held.cut_off);
      this.replace({
        ...held,
        stage: 'BOOKED',
        answer_by: null,
        players: held.players.map((player) => ({ ...player, held: !taken, paid: taken })),
        money: { ...held.money, collected_grosze: taken ? held.money.price_grosze : 0 },
      });
      return { status: 200, body: { outcome: 'BOOKED' as const, court_name: held.court_name } };
    });

    stub.on('post', '/api/v1/club/bookings/{booking_id}/refusal', ({ headers, params, body }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const held = this.find(params.booking_id);
      if (held === undefined) return notFound;
      const refused = this.stillWaiting(held);
      if (refused !== null) return refused;
      this.replace({
        ...held,
        stage: 'CALLED_OFF',
        called_off_reason: 'REFUSED',
        answer_by: null,
        refusal_reason: body?.reason?.trim() || null,
      });
      return { status: 204, body: undefined };
    });

    stub.on('get', '/api/v1/club/bookings/{booking_id}/free-courts', ({ headers, params }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const held = this.find(params.booking_id);
      if (held === undefined) return notFound;
      const refused = this.stillPlayable(held);
      if (refused !== null) return refused;
      return {
        status: 200,
        body: {
          courts: this.freeCourts(held).map((court) => ({ court_id: court.id, name: court.name })),
        },
      };
    });

    stub.on('post', '/api/v1/club/bookings/{booking_id}/move', ({ headers, params, body }) => {
      const signedOut = this.guard(headers.authorization);
      if (signedOut !== null) return signedOut;
      const held = this.find(params.booking_id);
      if (held === undefined) return notFound;
      const refused = this.stillPlayable(held);
      if (refused !== null) return refused;
      const to = this.freeCourts(held).find((court) => court.id === body.court_id);
      if (to === undefined) return conflict('court_not_free');
      this.replace({ ...held, court_id: to.id, court_name: to.name });
      return { status: 200, body: { court_id: to.id, name: to.name } };
    });

    stub.on(
      'post',
      '/api/v1/club/bookings/{booking_id}/cancellation',
      ({ headers, params, body }) => {
        const signedOut = this.guard(headers.authorization);
        if (signedOut !== null) return signedOut;
        const held = this.find(params.booking_id);
        if (held === undefined) return notFound;
        const refused = this.stillPlayable(held);
        if (refused !== null) return refused;
        // Every hold is let go and every share taken is refunded in full (#637).
        this.replace({
          ...held,
          stage: 'CALLED_OFF',
          called_off_reason: 'CANCELLED_BY_THE_CLUB',
          cancel_reason: body.reason,
          players: held.players.map((player) => ({ ...player, held: false })),
          money: { ...held.money, refunded_grosze: held.money.collected_grosze },
        });
        return { status: 204, body: undefined };
      },
    );

    return this;
  }
}

function conflict(code: string) {
  return { status: 409, body: refusal(code) } as const;
}
