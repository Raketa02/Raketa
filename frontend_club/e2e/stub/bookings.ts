/**
 * **The club's Raketa bookings, as the backend would keep them** (#547, #637, #669): each
 * booking's court, hour, players and money, and its status **folded on every read** from where it
 * stands and the clock, as `proposals/domain/club_bookings.py` folds it. The rules are the club
 * surface's own, from `backend/openapi.club.json`, kept just deep enough that a test can list a
 * day, move a game and cancel one without programming each reply. A test that is about one reply
 * overrides that handler with `stub.on`.
 */

import { randomUUID } from 'node:crypto';

import type { components } from '../../src/generated/schema';

import { refusal, type StubBackend } from './backend';
import { atClubHour, clubTime, dayFromToday } from './clock';
import { SEATS, type Court, type Exception } from './courts';

type ClubStatus = components['schemas']['ClubStatus'];
type ClubFilter = components['schemas']['ClubFilter'];
type ClubBooking = components['schemas']['ClubBookingSchema'];
type ErrorBody = components['schemas']['ErrorResponse'];

const HOUR_MS = 3_600_000;
/** The club's cut-off unless a test says otherwise: the setting's default, a day before (§16.6). */
const CUT_OFF_MS = 24 * HOUR_MS;

/**
 * Where a booking stands, before the clock is read: booked whole or with a seat open, or called
 * off. *Played* is read off the clock.
 */
export type Stage = 'BOOKED' | 'SEAT_OPEN' | 'CALLED_OFF';

/** **A booking as the fake keeps it**: the wire's row, but where it stands rather than its status. */
export type FakeBooking = Omit<ClubBooking, 'status' | 'ends_at' | 'may_move_or_cancel'> & {
  court_id: string;
  stage: Stage;
  /**
   * The cut-off the game was booked with, which the club's read never sends (§16.6): before it a
   * share is held, after it a share is taken (#637).
   */
  cut_off: string;
};

/** The names a game's players get unless a test names them, the first side first. */
const NAMES = ['Anna Nowak', 'Piotr Sikora', 'Kasia Wiśniewska', 'Marek Zając'];

/**
 * **A booking on `court` at `hour` of the local `day`**: booked and full, from an official group,
 * with a cut-off a day before it, unless the test says otherwise. A booked game's shares are held
 * while its cut-off is ahead and taken once it has passed, and only a taken share is collected
 * (#637). One with a seat open lacks its last player.
 */
export function booking(
  fields: { court: Court; day: string; hour: number; stage?: Stage } & Partial<
    Omit<FakeBooking, 'court_id' | 'court_name' | 'indoor' | 'sport' | 'starts_at' | 'stage'>
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
    indoor: court.indoor,
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
    ...rest,
  };
}

/** Each filter, by the status it shows. */
const FILTERED: Readonly<Record<Exclude<ClubFilter, 'ALL'>, ClubStatus>> = {
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

  status(held: FakeBooking): ClubStatus {
    if (held.stage === 'CALLED_OFF') return 'CALLED_OFF';
    if (Date.now() >= Date.parse(held.starts_at) + HOUR_MS) return 'PLAYED';
    return held.stage === 'SEAT_OPEN' ? 'SEAT_OPEN' : 'BOOKED';
  }

  /** Booked, whole or with a seat open, and its hour still ahead. */
  private stillToBePlayed(held: FakeBooking): boolean {
    return held.stage !== 'CALLED_OFF' && Date.now() < Date.parse(held.starts_at);
  }

  /** Bookings a court is held by until they are played: not called off, the hour not over. */
  ahead(): readonly FakeBooking[] {
    return this.bookings.filter(
      (held) => held.stage !== 'CALLED_OFF' && Date.now() < Date.parse(held.starts_at) + HOUR_MS,
    );
  }

  private row(held: FakeBooking): ClubBooking {
    return {
      booking_id: held.booking_id,
      starts_at: held.starts_at,
      ends_at: new Date(Date.parse(held.starts_at) + HOUR_MS).toISOString(),
      court_name: held.court_name,
      indoor: held.indoor,
      sport: held.sport,
      kind: held.kind,
      status: this.status(held),
      called_off_reason: held.called_off_reason,
      cancel_reason: held.cancel_reason,
      players: held.players,
      open_seats: held.open_seats,
      money: held.money,
      booked_from: held.booked_from,
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
    if (held.stage === 'CALLED_OFF') return conflict('booking_is_called_off');
    if (!this.stillToBePlayed(held)) return conflict('game_has_started');
    return null;
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
            seat_open: count('SEAT_OPEN'),
            called_off: count('CALLED_OFF'),
          },
          bookings:
            filter === 'ALL' ? rows : rows.filter((each) => each.status === FILTERED[filter]),
        },
      };
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
          courts: this.freeCourts(held).map((court) => ({
            court_id: court.id,
            name: court.name,
            indoor: court.indoor,
          })),
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
      this.replace({ ...held, court_id: to.id, court_name: to.name, indoor: to.indoor });
      return { status: 200, body: { court_id: to.id, name: to.name, indoor: to.indoor } };
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
        // Called off: every hold is let go and every share taken is refunded in full (#637). No
        // other court takes the game here (#672).
        this.replace({
          ...held,
          stage: 'CALLED_OFF',
          called_off_reason: 'CANCELLED_BY_THE_CLUB',
          cancel_reason: body.reason,
          players: held.players.map((player) => ({ ...player, held: false })),
          money: { ...held.money, refunded_grosze: held.money.collected_grosze },
        });
        return { status: 200, body: { outcome: 'CALLED_OFF' as const, court: null } };
      },
    );

    return this;
  }
}

function conflict(code: string) {
  return { status: 409, body: refusal(code) } as const;
}
