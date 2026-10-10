import type { components } from '@/generated/schema';

import { toBookedGame, toHome } from './homeMappers';

type Wire = components['schemas'];

const tile = (extra: Partial<Wire['BookedTileSchema']> = {}): Wire['BookedTileSchema'] => ({
  player_id: 'p-1',
  is_you: false,
  name: 'Piotr Sowa',
  photo_id: null,
  photo_url: null,
  level: 2.95,
  paid: true,
  checked_in: false,
  ...extra,
});

const homeGame = (extra: Partial<Wire['HomeGameSchema']> = {}): Wire['HomeGameSchema'] => ({
  booking_id: 'b-1',
  game_id: 'g-1',
  pool_id: 'group-1',
  sport: 'PADEL',
  kind: 'COMPETITIVE',
  status: 'BOOKED',
  called_off_reason: null,
  club_cancel_reason: null,
  uncounted_reason: null,
  open_seats: 0,
  needs_you: false,
  filling_again: false,
  club_confirms: false,
  starts_at: '2026-10-03T14:00:00Z',
  club: { id: 'club-1', name: 'Bonarka Arena' },
  court_name: 'Court 2',
  sides: { yours: [tile({ player_id: 'me', is_you: true })], theirs: [tile()] },
  money: {
    share_grosze: 2800,
    paid: false,
    share_state: 'HELD',
    held_from: null,
    taken_at: '2026-10-02T14:00:00Z',
    free_to_leave_until: '2026-10-02T14:00:00Z',
    refunded_grosze: null,
  },
  answer_by: null,
  payment_due_by: null,
  your_payment_due_by: null,
  time_to: null,
  ...extra,
});

/** The money as a server older than Q113 sends it — the cut-off, and no share's state (#637). */
const OLDER_MONEY = {
  share_grosze: 2800,
  paid: true,
  free_to_leave_until: '2026-10-02T14:00:00Z',
  refunded_grosze: null,
} as Wire['BookedMoneySchema'];

describe('toHome', () => {
  it('reads the badge, the clock and every card, the sides with their paid and check-in', () => {
    const home = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 2,
      games: [
        homeGame({
          sides: {
            yours: [tile({ player_id: 'me', is_you: true })],
            theirs: [tile({ checked_in: true })],
          },
        }),
      ],
    });

    expect(home).toEqual({
      readAt: '2026-10-01T08:00:00Z',
      needingYou: 2,
      games: [
        {
          bookingId: 'b-1',
          gameId: 'g-1',
          groupId: 'group-1',
          sport: 'padel',
          kind: 'competitive',
          status: 'BOOKED',
          openSeats: 0,
          needsYou: false,
          startsAt: '2026-10-03T14:00:00Z',
          club: { id: 'club-1', name: 'Bonarka Arena' },
          courtName: 'Court 2',
          sides: {
            yours: [
              {
                playerId: 'me',
                isYou: true,
                isIn: false,
                paid: true,
                checkedIn: false,
                name: 'Piotr Sowa',
                level: 2.95,
              },
            ],
            theirs: [
              {
                playerId: 'p-1',
                isYou: false,
                isIn: false,
                paid: true,
                checkedIn: true,
                name: 'Piotr Sowa',
                level: 2.95,
              },
            ],
          },
          money: {
            shareGrosze: 2800,
            paid: false,
            shareState: 'HELD',
            takenAt: '2026-10-02T14:00:00Z',
            freeToLeaveUntil: '2026-10-02T14:00:00Z',
          },
        },
      ],
    });
  });

  it('leaves off what the wire does not hold, rather than a null', () => {
    const [game] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [
        homeGame({
          club: { id: 'club-1', name: null },
          sides: {
            yours: [tile({ name: null, level: null, photo_url: null, paid: false })],
            theirs: [],
          },
          money: {
            share_grosze: 2800,
            paid: false,
            share_state: null,
            held_from: null,
            taken_at: null,
            free_to_leave_until: null,
            refunded_grosze: null,
          },
        }),
      ],
    }).games;

    expect(game?.club).toEqual({ id: 'club-1' });
    expect(game?.sides.yours[0]).toEqual({
      playerId: 'p-1',
      isYou: false,
      isIn: false,
      paid: false,
      checkedIn: false,
    });
    expect(game?.money).toEqual({ shareGrosze: 2800, paid: false });
  });

  it('reads a game waiting for the club with no Game and no court yet', () => {
    const [game] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [homeGame({ status: 'WAITING_FOR_THE_CLUB', game_id: null, court_name: null })],
    }).games;

    expect(game).not.toHaveProperty('gameId');
    expect(game).not.toHaveProperty('courtName');
  });

  it('carries when the club answers, and nothing from a null or an older server’s silence', () => {
    const [waiting, unset, older] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [
        homeGame({ status: 'WAITING_FOR_THE_CLUB', answer_by: '2026-10-01T09:00:00Z' }),
        homeGame({ status: 'WAITING_FOR_THE_CLUB' }),
        homeGame({ status: 'WAITING_FOR_THE_CLUB', answer_by: undefined }),
      ],
    }).games;

    expect(waiting?.answerBy).toBe('2026-10-01T09:00:00Z');
    expect(unset).not.toHaveProperty('answerBy');
    expect(older).not.toHaveProperty('answerBy');
  });

  it('carries the payment a game waits for, the reader’s own time, and nothing from a null or an older server’s silence', () => {
    const [everybody, payer, unset, older] = toHome({
      read_at: '2026-10-06T12:10:00Z',
      needing_you: 0,
      games: [
        homeGame({ status: 'WAITING_FOR_A_PAYMENT', payment_due_by: '2026-10-06T12:40:00Z' }),
        homeGame({
          status: 'WAITING_FOR_A_PAYMENT',
          payment_due_by: '2026-10-06T12:40:00Z',
          your_payment_due_by: '2026-10-06T12:40:00Z',
        }),
        homeGame({ status: 'WAITING_FOR_A_PAYMENT' }),
        homeGame({ payment_due_by: undefined, your_payment_due_by: undefined }),
      ],
    }).games;

    expect(everybody?.status).toBe('WAITING_FOR_A_PAYMENT');
    expect(everybody?.paymentDueBy).toBe('2026-10-06T12:40:00Z');
    expect(everybody).not.toHaveProperty('yourPaymentDueBy');
    expect(payer?.yourPaymentDueBy).toBe('2026-10-06T12:40:00Z');
    expect(unset).not.toHaveProperty('paymentDueBy');
    expect(older).not.toHaveProperty('paymentDueBy');
    expect(older).not.toHaveProperty('yourPaymentDueBy');
  });

  /**
   * **Held, checked or taken** (#637, #639; Q113) — the share's state and the two instants it
   * switches at, and nothing from an older server's silence.
   */
  it('carries where the share stands and when it is held and taken', () => {
    const checked = {
      ...homeGame().money,
      share_state: 'CHECKED',
      held_from: '2026-09-28T14:00:00Z',
    } as const;
    const [held, check, older] = toHome({
      read_at: '2026-09-27T08:00:00Z',
      needing_you: 0,
      games: [homeGame(), homeGame({ money: checked }), homeGame({ money: OLDER_MONEY })],
    }).games;

    expect(held?.money).toMatchObject({ shareState: 'HELD', takenAt: '2026-10-02T14:00:00Z' });
    expect(held?.money).not.toHaveProperty('heldFrom');
    expect(check?.money).toMatchObject({
      shareState: 'CHECKED',
      heldFrom: '2026-09-28T14:00:00Z',
      takenAt: '2026-10-02T14:00:00Z',
    });
    expect(older?.money).toEqual({
      shareGrosze: 2800,
      paid: true,
      freeToLeaveUntil: '2026-10-02T14:00:00Z',
    });
  });

  it('reads why a game is off or uncounted, the seats open and what came back', () => {
    const [off, short, open] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 1,
      games: [
        homeGame({
          status: 'CALLED_OFF',
          called_off_reason: 'SHORT_AT_THE_CUT_OFF',
          money: {
            share_grosze: 2800,
            paid: true,
            share_state: null,
            held_from: null,
            taken_at: null,
            free_to_leave_until: null,
            refunded_grosze: 2800,
          },
        }),
        homeGame({ status: 'UNCOUNTED', uncounted_reason: 'SEAT_EMPTY' }),
        homeGame({ status: 'SEAT_OPEN', open_seats: 2 }),
      ],
    }).games;

    expect(off).toMatchObject({
      calledOffReason: 'SHORT_AT_THE_CUT_OFF',
      money: { refundedGrosze: 2800 },
    });
    expect(short).toMatchObject({ uncountedReason: 'SEAT_EMPTY' });
    expect(open).toMatchObject({ openSeats: 2 });
    expect(open).not.toHaveProperty('calledOffReason');
    expect(open).not.toHaveProperty('uncountedReason');
  });

  /**
   * **A full game gone back to filling** (#624, Q106) carries which way its line ends — asked of the
   * club again, or booked at once — and a booked game carries nothing, from an older server too.
   */
  it('reads a full game gone back to filling, and whether its club is asked again', () => {
    const [atTheClub, atOnce, booked, older] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [
        homeGame({ status: 'SEAT_OPEN', open_seats: 1, filling_again: true, club_confirms: true }),
        homeGame({ status: 'SEAT_OPEN', open_seats: 1, filling_again: true, club_confirms: false }),
        homeGame({ status: 'SEAT_OPEN', open_seats: 1, club_confirms: true }),
        homeGame({ status: 'SEAT_OPEN', filling_again: undefined, club_confirms: undefined }),
      ],
    }).games;

    expect(atTheClub?.fillingAgain).toEqual({ clubConfirms: true });
    expect(atOnce?.fillingAgain).toEqual({ clubConfirms: false });
    expect(booked).not.toHaveProperty('fillingAgain');
    expect(older).not.toHaveProperty('fillingAgain');
  });

  it('reads the two ways a game gone back to filling is called off', () => {
    const [passed, lost] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [
        homeGame({
          status: 'CALLED_OFF',
          called_off_reason: 'BOOK_BY_PASSED',
          filling_again: true,
        }),
        homeGame({
          status: 'CALLED_OFF',
          called_off_reason: 'COURT_HOUR_LOST',
          filling_again: true,
        }),
      ],
    }).games;

    expect(passed?.calledOffReason).toBe('BOOK_BY_PASSED');
    expect(lost?.calledOffReason).toBe('COURT_HOUR_LOST');
  });

  it('drops a card in a sport this build cannot name, and keeps the rest', () => {
    const home = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [homeGame({ sport: 'CURLING' as Wire['Sport'] }), homeGame({ booking_id: 'b-2' })],
    });

    expect(home.games.map((one) => one.bookingId)).toEqual(['b-2']);
  });
});

describe('toBookedGame', () => {
  const details = (
    extra: Partial<Wire['BookingDetailsResponse']> = {},
  ): Wire['BookingDetailsResponse'] => ({
    booking_id: 'b-1',
    game_id: 'g-1',
    pool_id: 'group-1',
    sport: 'PADEL',
    kind: 'FOR_FUN',
    read_at: '2026-10-03T08:00:00Z',
    status: 'BOOKED',
    called_off_reason: null,
    club_cancel_reason: null,
    uncounted_reason: null,
    open_seats: 0,
    needs_you: false,
    filling_again: false,
    club_confirms: false,
    starts_at: '2026-10-03T14:00:00Z',
    ends_at: '2026-10-03T15:00:00Z',
    where: { id: 'club-1', name: 'Bonarka Arena', distance_km: 3.1 },
    court_name: 'Court 2',
    sides: { yours: [tile({ player_id: 'me', is_you: true })], theirs: [tile()] },
    money: {
      share_grosze: 2800,
      paid: true,
      share_state: 'TAKEN',
      held_from: null,
      taken_at: '2026-10-02T14:00:00Z',
      free_to_leave_until: null,
      refunded_grosze: null,
    },
    shows_forecast: true,
    check_in: { short_code: 'K7M2QX', qr_payload: 'RAKETA-CHECK-IN:1:b-1:me:K7M2QX' },
    leaving: null,
    rescue: null,
    answer_by: null,
    payment_due_by: null,
    your_payment_due_by: null,
    time_to: null,
    ...extra,
  });

  it('reads the details, WHERE with its distance and the code for the desk', () => {
    expect(toBookedGame(details())).toMatchObject({
      bookingId: 'b-1',
      gameId: 'g-1',
      groupId: 'group-1',
      sport: 'padel',
      kind: 'forFun',
      readAt: '2026-10-03T08:00:00Z',
      endsAt: '2026-10-03T15:00:00Z',
      where: { id: 'club-1', name: 'Bonarka Arena', distanceKm: 3.1 },
      courtName: 'Court 2',
      money: { shareGrosze: 2800, paid: true },
      showsForecast: true,
      checkIn: { shortCode: 'K7M2QX', qrPayload: 'RAKETA-CHECK-IN:1:b-1:me:K7M2QX' },
    });
  });

  it('has no distance for a reader with no Location area, and no code off the day', () => {
    const game = toBookedGame(
      details({ where: { id: 'club-1', name: null, distance_km: null }, check_in: null }),
    );

    expect(game?.where).toEqual({ id: 'club-1' });
    expect(game).not.toHaveProperty('checkIn');
  });

  it('carries where the share stands on the money row, as Home’s card does (Q113)', () => {
    const money = { ...homeGame().money, share_grosze: 4000 };

    expect(toBookedGame(details({ money }))?.money).toEqual({
      shareGrosze: 4000,
      paid: false,
      shareState: 'HELD',
      takenAt: '2026-10-02T14:00:00Z',
      freeToLeaveUntil: '2026-10-02T14:00:00Z',
    });
  });

  it('reads what leaving would cost now, and nothing where there is no button', () => {
    const before = toBookedGame(
      details({
        leaving: { kind: 'BEFORE_THE_CUT_OFF', refund_grosze: null, card_fee_grosze: null },
      }),
    );
    const after = toBookedGame(
      details({
        leaving: { kind: 'AFTER_THE_CUT_OFF', refund_grosze: 2758, card_fee_grosze: 142 },
      }),
    );

    expect(before?.leaving).toEqual({ kind: 'BEFORE_THE_CUT_OFF' });
    expect(after?.leaving).toEqual({ kind: 'AFTER_THE_CUT_OFF' });
    expect(toBookedGame(details())).not.toHaveProperty('leaving');
  });

  it('reads the open seat offered from outside, and nothing for a player in the game', () => {
    const game = toBookedGame(
      details({ rescue: { deadline: '2026-10-02T14:00:00Z', fills_by_the_cut_off: true } }),
    );

    expect(game?.rescue).toEqual({ deadline: '2026-10-02T14:00:00Z', fillsByTheCutOff: true });
    expect(toBookedGame(details())).not.toHaveProperty('rescue');
    expect(toBookedGame(details({ rescue: undefined }))).not.toHaveProperty('rescue');
  });

  it('carries when the club answers, and nothing from a null or an older server’s silence', () => {
    const waiting = toBookedGame(
      details({ status: 'WAITING_FOR_THE_CLUB', answer_by: '2026-10-03T09:00:00Z' }),
    );

    expect(waiting?.answerBy).toBe('2026-10-03T09:00:00Z');
    expect(toBookedGame(details())).not.toHaveProperty('answerBy');
    expect(toBookedGame(details({ answer_by: undefined }))).not.toHaveProperty('answerBy');
  });

  it('carries the payment a game waits for in detail, as Home does', () => {
    const waiting = toBookedGame(
      details({
        status: 'WAITING_FOR_A_PAYMENT',
        payment_due_by: '2026-10-06T12:40:00Z',
        your_payment_due_by: '2026-10-06T12:40:00Z',
      }),
    );

    expect(waiting).toMatchObject({
      status: 'WAITING_FOR_A_PAYMENT',
      paymentDueBy: '2026-10-06T12:40:00Z',
      yourPaymentDueBy: '2026-10-06T12:40:00Z',
    });
    expect(toBookedGame(details())).not.toHaveProperty('paymentDueBy');
  });

  it('reads a full game gone back to filling in detail, as Home does', () => {
    const filling = toBookedGame(
      details({
        status: 'SEAT_OPEN',
        open_seats: 1,
        filling_again: true,
        club_confirms: true,
        leaving: null,
      }),
    );

    expect(filling?.fillingAgain).toEqual({ clubConfirms: true });
    expect(filling).not.toHaveProperty('leaving');
    expect(toBookedGame(details())).not.toHaveProperty('fillingAgain');
  });

  it('is nothing for a sport this build cannot name', () => {
    expect(toBookedGame(details({ sport: 'CURLING' as Wire['Sport'] }))).toBeUndefined();
  });
});
