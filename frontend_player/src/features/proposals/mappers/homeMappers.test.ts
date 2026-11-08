import type { components } from '@/generated/schema';

import { toBookedGame, toHome } from './homeMappers';

type Wire = components['schemas'];

const tile = (extra: Partial<Wire['BookedTileSchema']> = {}): Wire['BookedTileSchema'] => ({
  player_id: 'p-1',
  is_you: false,
  nickname: 'piotr.s',
  photo_id: null,
  photo_url: null,
  level: 2.95,
  paid: true,
  friend: false,
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
  starts_at: '2026-10-03T14:00:00Z',
  club: { id: 'club-1', name: 'Bonarka Arena' },
  court_name: 'Court 2',
  indoor: true,
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
  payment_due_by: null,
  your_payment_due_by: null,
  time_to: null,
  friends_game: null,
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
  it('reads the badge, the clock and every card, the sides with their paid', () => {
    const home = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 2,
      friends_games: [],
      level_asks: [],
      friend_requests: [],
      games: [
        homeGame({
          sides: {
            yours: [tile({ player_id: 'me', is_you: true })],
            theirs: [tile()],
          },
        }),
      ],
    });

    expect(home).toEqual({
      readAt: '2026-10-01T08:00:00Z',
      needingYou: 2,
      friendRequests: [],
      friendsGames: [],
      levelAsks: [],
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
          indoor: true,
          sides: {
            yours: [
              {
                playerId: 'me',
                isYou: true,
                isIn: false,
                paid: true,
                name: 'piotr.s',
                level: 2.95,
              },
            ],
            theirs: [
              {
                playerId: 'p-1',
                isYou: false,
                isIn: false,
                paid: true,
                name: 'piotr.s',
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
      friends_games: [],
      level_asks: [],
      friend_requests: [],
      games: [
        homeGame({
          club: { id: 'club-1', name: null },
          sides: {
            yours: [tile({ nickname: null, level: null, photo_url: null, paid: false })],
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
    });
    expect(game?.money).toEqual({ shareGrosze: 2800, paid: false });
  });

  it('reads a game waiting for one payment with no Game and no court yet', () => {
    const [game] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      friends_games: [],
      level_asks: [],
      friend_requests: [],
      games: [
        homeGame({
          status: 'WAITING_FOR_A_PAYMENT',
          game_id: null,
          court_name: null,
          indoor: null,
        }),
      ],
    }).games;

    expect(game).not.toHaveProperty('gameId');
    expect(game).not.toHaveProperty('courtName');
  });

  it('carries the payment a game waits for, the reader’s own time, and nothing from a null or an older server’s silence', () => {
    const [everybody, payer, unset, older] = toHome({
      read_at: '2026-10-06T12:10:00Z',
      needing_you: 0,
      friends_games: [],
      level_asks: [],
      friend_requests: [],
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

  it('carries what the time is for — to fix the card or to pay (#638) — and nothing from a null', () => {
    const [fixing, paying, unset, older] = toHome({
      read_at: '2026-10-06T12:10:00Z',
      needing_you: 0,
      friends_games: [],
      level_asks: [],
      friend_requests: [],
      games: [
        homeGame({ your_payment_due_by: '2026-10-06T12:40:00Z', time_to: 'FIX_THE_CARD' }),
        homeGame({
          status: 'WAITING_FOR_A_PAYMENT',
          your_payment_due_by: '2026-10-06T12:40:00Z',
          time_to: 'PAY',
        }),
        homeGame(),
        homeGame({ time_to: undefined }),
      ],
    }).games;

    expect(fixing?.timeTo).toBe('FIX_THE_CARD');
    expect(paying?.timeTo).toBe('PAY');
    expect(unset).not.toHaveProperty('timeTo');
    expect(older).not.toHaveProperty('timeTo');
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
      friends_games: [],
      level_asks: [],
      friend_requests: [],
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
      friends_games: [],
      level_asks: [],
      friend_requests: [],
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
   * **A full game gone back to filling** (#624, Q106) is marked so, and a booked game carries
   * nothing, from an older server too.
   */
  it('reads a full game gone back to filling', () => {
    const [filling, booked, older] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      friends_games: [],
      level_asks: [],
      friend_requests: [],
      games: [
        homeGame({ status: 'SEAT_OPEN', open_seats: 1, filling_again: true }),
        homeGame({ status: 'SEAT_OPEN', open_seats: 1 }),
        homeGame({ status: 'SEAT_OPEN', filling_again: undefined }),
      ],
    }).games;

    expect(filling?.fillingAgain).toBe(true);
    expect(booked).not.toHaveProperty('fillingAgain');
    expect(older).not.toHaveProperty('fillingAgain');
  });

  it('reads the two ways a game gone back to filling is called off', () => {
    const [passed, lost] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      friends_games: [],
      level_asks: [],
      friend_requests: [],
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
      friends_games: [],
      level_asks: [],
      friend_requests: [],
      games: [homeGame({ sport: 'CURLING' as Wire['Sport'] }), homeGame({ booking_id: 'b-2' })],
    });

    expect(home.games.map((one) => one.bookingId)).toEqual(['b-2']);
  });
});

describe('toHome — the friend requests waiting on the reader (#753)', () => {
  const request = (
    extra: Partial<Wire['HomeFriendRequestSchema']> = {},
  ): Wire['HomeFriendRequestSchema'] => ({
    player_id: 'p-ines',
    nickname: 'ines.d',
    photo_id: 'f-1',
    photo_url: 'https://photos.example/ines.jpg',
    asked_at: '2026-10-01T07:00:00Z',
    by_link: false,
    from_ranking: false,
    group: { id: 'group-1', name: 'Kazimierz crew' },
    sport: 'PADEL',
    level: 3.4,
    player_score: 98,
    reliability_band: 'VERY_HIGH',
    ...extra,
  });
  const home = (requests: Wire['HomeFriendRequestSchema'][]) =>
    toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [],
      friends_games: [],
      level_asks: [],
      friend_requests: requests,
    });

  it('reads each card in the order served: who, where, their level and reliability', () => {
    expect(
      home([request(), request({ player_id: 'p-2', nickname: 'kuba.w' })]).friendRequests,
    ).toEqual([
      {
        playerId: 'p-ines',
        nickname: 'ines.d',
        photoUrl: 'https://photos.example/ines.jpg',
        byLink: false,
        fromRanking: false,
        group: { id: 'group-1', name: 'Kazimierz crew' },
        sport: 'padel',
        level: 3.4,
        playerScore: 98,
        reliabilityBand: 'VERY_HIGH',
      },
      expect.objectContaining({ playerId: 'p-2', nickname: 'kuba.w' }),
    ]);
  });

  it('leaves off what the wire left null — a link’s request names no group and no sport', () => {
    expect(
      home([request({ by_link: true, group: null, sport: null, level: null, photo_url: null })])
        .friendRequests,
    ).toEqual([
      {
        playerId: 'p-ines',
        nickname: 'ines.d',
        byLink: true,
        fromRanking: false,
        playerScore: 98,
        reliabilityBand: 'VERY_HIGH',
      },
    ]);
  });

  it('reads a request from the ranking with the ranking’s sport, and no group (#779)', () => {
    expect(
      home([request({ from_ranking: true, group: null, sport: 'SQUASH', level: 2.4 })])
        .friendRequests,
    ).toEqual([
      expect.objectContaining({ fromRanking: true, byLink: false, sport: 'squash', level: 2.4 }),
    ]);
    expect(
      home([request({ from_ranking: true, group: null })]).friendRequests[0],
    ).not.toHaveProperty('group');
  });
});

describe('toSeat — the friend tag (#753)', () => {
  it('marks the reader’s own friends, and only them', () => {
    const [friend, other] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      friends_games: [],
      level_asks: [],
      friend_requests: [],
      games: [homeGame({ sides: { yours: [tile({ friend: true })], theirs: [tile()] } })],
    }).games[0]!.sides.yours.concat(
      toHome({
        read_at: '2026-10-01T08:00:00Z',
        needing_you: 0,
        friends_games: [],
        level_asks: [],
        friend_requests: [],
        games: [homeGame({ sides: { yours: [tile()], theirs: [] } })],
      }).games[0]!.sides.yours,
    );
    expect(friend).toEqual(expect.objectContaining({ friend: true }));
    expect(other).not.toHaveProperty('friend');
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
    starts_at: '2026-10-03T14:00:00Z',
    ends_at: '2026-10-03T15:00:00Z',
    where: { id: 'club-1', name: 'Bonarka Arena', distance_km: 3.1 },
    court_name: 'Court 2',
    indoor: true,
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
    leaving: null,
    rescue: null,
    payment_due_by: null,
    your_payment_due_by: null,
    time_to: null,
    played_with: [],
    friends_game: null,
    ...extra,
  });

  it('reads the details and WHERE with its distance', () => {
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
    });
  });

  it('reads PLAYED WITH: everybody else, with where the reader stands with each (#754)', () => {
    const game = toBookedGame(
      details({
        played_with: [
          { player_id: 'p-1', relation: 'FRIEND' },
          { player_id: 'p-2', relation: 'NONE' },
        ],
      }),
    );

    expect(game?.playedWith).toEqual([
      { playerId: 'p-1', relation: 'FRIEND' },
      { playerId: 'p-2', relation: 'NONE' },
    ]);
    expect(toBookedGame(details())?.playedWith).toEqual([]);
  });

  it('has no distance for a reader with no Location area', () => {
    const game = toBookedGame(details({ where: { id: 'club-1', name: null, distance_km: null } }));

    expect(game?.where).toEqual({ id: 'club-1' });
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
        leaving: { kind: 'AFTER_THE_CUT_OFF', refund_grosze: 3824, card_fee_grosze: 176 },
      }),
    );

    expect(before?.leaving).toEqual({ kind: 'BEFORE_THE_CUT_OFF' });
    expect(after?.leaving).toEqual({
      kind: 'AFTER_THE_CUT_OFF',
      lateRefund: { backGrosze: 3824, keptGrosze: 176 },
    });
    expect(toBookedGame(details())).not.toHaveProperty('leaving');
  });

  /** No figure while the fee kept isn't known (#641) — and a payment's wait quotes nought, which is no refund. */
  it('carries no quote after the cut-off while the fee kept is unknown, nor while a payment is awaited', () => {
    const unknown = toBookedGame(
      details({
        leaving: { kind: 'AFTER_THE_CUT_OFF', refund_grosze: null, card_fee_grosze: null },
      }),
    );
    const waiting = toBookedGame(
      details({
        leaving: { kind: 'WHILE_WAITING_FOR_A_PAYMENT', refund_grosze: 0, card_fee_grosze: 0 },
      }),
    );

    expect(unknown?.leaving).toEqual({ kind: 'AFTER_THE_CUT_OFF' });
    expect(waiting?.leaving).toEqual({ kind: 'WHILE_WAITING_FOR_A_PAYMENT' });
  });

  it('reads the open seat offered from outside, and nothing for a player in the game', () => {
    const game = toBookedGame(
      details({ rescue: { deadline: '2026-10-02T14:00:00Z', fills_by_the_cut_off: true } }),
    );

    expect(game?.rescue).toEqual({ deadline: '2026-10-02T14:00:00Z', fillsByTheCutOff: true });
    expect(toBookedGame(details())).not.toHaveProperty('rescue');
    expect(toBookedGame(details({ rescue: undefined }))).not.toHaveProperty('rescue');
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
    expect(
      toBookedGame(
        details({ your_payment_due_by: '2026-10-06T12:40:00Z', time_to: 'FIX_THE_CARD' }),
      ),
    ).toMatchObject({ timeTo: 'FIX_THE_CARD' });
  });

  it('reads a full game gone back to filling in detail, as Home does', () => {
    const filling = toBookedGame(
      details({
        status: 'SEAT_OPEN',
        open_seats: 1,
        filling_again: true,
        leaving: null,
      }),
    );

    expect(filling?.fillingAgain).toBe(true);
    expect(filling).not.toHaveProperty('leaving');
    expect(toBookedGame(details())).not.toHaveProperty('fillingAgain');
  });

  it('is nothing for a sport this build cannot name', () => {
    expect(toBookedGame(details({ sport: 'CURLING' as Wire['Sport'] }))).toBeUndefined();
  });
});

describe('a friends game (#759)', () => {
  const friendsGame = (
    extra: Partial<Wire['FriendsGameSchema']> = {},
  ): Wire['FriendsGameSchema'] => ({
    sender_id: 'tomek',
    sender_nickname: 'tomek.k',
    you_are_the_sender: false,
    pay_mode: 'SPLIT_THE_COST',
    seats: [
      { player_id: 'tomek', state: 'IN', waiting_until: null, can_invite: false, can_open: false },
      {
        player_id: 'me',
        state: 'WAITING',
        waiting_until: '2026-10-02T08:00:00Z',
        can_invite: false,
        can_open: false,
      },
    ],
    friends_in: 0,
    friends_seated: 1,
    your_invitation_until: '2026-10-02T08:00:00Z',
    can_call_off: false,
    ...extra,
  });

  const invitation = (
    extra: Partial<Wire['HomeFriendsGameSchema']> = {},
  ): Wire['HomeFriendsGameSchema'] => ({
    booking_id: 'b-9',
    pool_id: 'group-1',
    sport: 'TENNIS',
    kind: 'FOR_FUN',
    starts_at: '2026-10-03T08:00:00Z',
    club: { id: 'club-1', name: 'Ogrody 33' },
    court_name: 'Court 3',
    indoor: false,
    share_grosze: 2500,
    sides: { yours: [tile({ player_id: 'me', is_you: true })], theirs: [tile()] },
    friends_game: friendsGame(),
    ...extra,
  });

  const home = (extra: Partial<Wire['HomeResponse']> = {}): Wire['HomeResponse'] => ({
    read_at: '2026-10-01T08:00:00Z',
    needing_you: 0,
    games: [],
    friend_requests: [],
    friends_games: [],
    level_asks: [],
    ...extra,
  });

  it('reads each invitation on Home with its game’s facts, the soonest to end as served', () => {
    expect(toHome(home({ friends_games: [invitation()] })).friendsGames).toEqual([
      {
        bookingId: 'b-9',
        groupId: 'group-1',
        sport: 'tennis',
        kind: 'forFun',
        startsAt: '2026-10-03T08:00:00Z',
        club: { id: 'club-1', name: 'Ogrody 33' },
        courtName: 'Court 3',
        indoor: false,
        shareGrosze: 2500,
        sides: expect.objectContaining({ yours: [expect.objectContaining({ playerId: 'me' })] }),
        friendsGame: {
          senderId: 'tomek',
          senderNickname: 'tomek.k',
          youAreTheSender: false,
          payMode: 'SPLIT_THE_COST',
          seats: [
            { playerId: 'tomek', state: 'IN' },
            { playerId: 'me', state: 'WAITING', waitingUntil: '2026-10-02T08:00:00Z' },
          ],
          friendsIn: 0,
          friendsSeated: 1,
          yourInvitationUntil: '2026-10-02T08:00:00Z',
          canCallOff: false,
        },
      },
    ]);
  });

  it('drops an invitation in a sport this build cannot name, and reads none from an older server', () => {
    expect(
      toHome(home({ friends_games: [invitation({ sport: 'CURLING' as Wire['Sport'] })] }))
        .friendsGames,
    ).toEqual([]);
    const older = home();
    delete (older as Partial<Wire['HomeResponse']>).friends_games;
    expect(toHome(older).friendsGames).toEqual([]);
  });

  it('reads the facts on a Home card, an unnamed sender left off, and none on a game a fill booked', () => {
    const read = toHome(
      home({
        games: [
          homeGame({
            friends_game: friendsGame({
              sender_nickname: null,
              you_are_the_sender: true,
              pay_mode: 'WHOLE_COURT',
              your_invitation_until: null,
              can_call_off: true,
            }),
          }),
          homeGame({ booking_id: 'b-2' }),
        ],
      }),
    );
    expect(read.games[0]?.friendsGame).toEqual(
      expect.objectContaining({ youAreTheSender: true, payMode: 'WHOLE_COURT', canCallOff: true }),
    );
    expect(read.games[0]?.friendsGame).not.toHaveProperty('senderNickname');
    expect(read.games[0]?.friendsGame).not.toHaveProperty('yourInvitationUntil');
    expect(read.games[1]).not.toHaveProperty('friendsGame');
  });

  it('reads an empty seat’s name, its invitations and what the reader may do (#760)', () => {
    const read = toHome(
      home({
        games: [
          homeGame({
            friends_game: friendsGame({
              seats: [
                {
                  player_id: 'tomek',
                  state: 'IN',
                  waiting_until: null,
                  can_invite: false,
                  can_open: false,
                },
                {
                  player_id: 'ania',
                  state: 'CANT_MAKE_IT',
                  waiting_until: null,
                  seat_of: 'ania',
                  invitations: [
                    {
                      player_id: 'piotr',
                      nickname: 'piotr.s',
                      until: '2026-10-02T06:00:00Z',
                      invited_by_you: true,
                    },
                    {
                      player_id: 'kuba',
                      nickname: null,
                      until: '2026-10-02T07:00:00Z',
                      invited_by_you: false,
                    },
                  ],
                  can_invite: true,
                  can_open: true,
                },
                {
                  player_id: 'ewa',
                  state: 'SEAT_OPEN',
                  waiting_until: null,
                  seat_of: 'ewa',
                  can_invite: true,
                  can_open: false,
                },
              ],
            }),
          }),
        ],
      }),
    );

    expect(read.games[0]?.friendsGame?.seats).toEqual([
      { playerId: 'tomek', state: 'IN' },
      {
        playerId: 'ania',
        state: 'CANT_MAKE_IT',
        seatOf: 'ania',
        invitations: [
          { playerId: 'piotr', nickname: 'piotr.s', until: '2026-10-02T06:00:00Z' },
          { playerId: 'kuba', until: '2026-10-02T07:00:00Z' },
        ],
        canInvite: true,
        canOpen: true,
      },
      { playerId: 'ewa', state: 'SEAT_OPEN', seatOf: 'ewa', canInvite: true },
    ]);
  });
});

describe('toHome — a friend’s ask for a level waiting on the reader (#765)', () => {
  const asker = (
    extra: Partial<Wire['HomeLevelAskerSchema']> = {},
  ): Wire['HomeLevelAskerSchema'] => ({
    player_id: 'p-tomek',
    nickname: 'tomek.k',
    photo_id: 'f-1',
    photo_url: 'https://photos.example/tomek.jpg',
    ...extra,
  });
  const home = (asks: Wire['HomeLevelAskSchema'][]): Wire['HomeResponse'] => ({
    read_at: '2026-10-01T08:00:00Z',
    needing_you: 0,
    games: [],
    friend_requests: [],
    friends_games: [],
    level_asks: asks,
  });

  it('reads one card per sport in the order served, its askers newest first', () => {
    expect(
      toHome(
        home([
          {
            sport: 'PADEL',
            askers: [asker(), asker({ player_id: 'p-kuba', nickname: 'kuba.w', photo_url: null })],
          },
          { sport: 'SQUASH', askers: [asker({ player_id: 'p-ania', nickname: 'ania.m' })] },
        ]),
      ).levelAsks,
    ).toEqual([
      {
        sport: 'padel',
        askers: [
          {
            playerId: 'p-tomek',
            nickname: 'tomek.k',
            photoUrl: 'https://photos.example/tomek.jpg',
          },
          { playerId: 'p-kuba', nickname: 'kuba.w' },
        ],
      },
      {
        sport: 'squash',
        askers: [
          { playerId: 'p-ania', nickname: 'ania.m', photoUrl: 'https://photos.example/tomek.jpg' },
        ],
      },
    ]);
  });

  it('drops a card in a sport this build cannot name, one with nobody on it, and reads none from an older server', () => {
    expect(
      toHome(
        home([
          { sport: 'CURLING' as Wire['Sport'], askers: [asker()] },
          { sport: 'TENNIS', askers: [] },
        ]),
      ).levelAsks,
    ).toEqual([]);
    const older = home([]);
    delete (older as Partial<Wire['HomeResponse']>).level_asks;
    expect(toHome(older).levelAsks).toEqual([]);
  });
});

describe('toHome — the trophy left of the bell (#775)', () => {
  const home = (ranking?: Wire['HomeRankingSchema'] | null): Wire['HomeResponse'] => ({
    read_at: '2026-10-01T08:00:00Z',
    needing_you: 0,
    games: [],
    friend_requests: [],
    friends_games: [],
    level_asks: [],
    ...(ranking === undefined ? {} : { ranking }),
  });

  it('reads the sport of the latest result and both places in it', () => {
    expect(toHome(home({ sport: 'PADEL', general_place: 7, friends_place: 4 })).ranking).toEqual({
      sport: 'padel',
      generalPlace: 7,
      friendsPlace: 4,
    });
  });

  it('leaves out a place the reader has none in, so the trophy draws no number', () => {
    expect(
      toHome(home({ sport: 'TENNIS', general_place: null, friends_place: null })).ranking,
    ).toEqual({ sport: 'tennis' });
  });

  it('is absent with no result anywhere, from an older server, and in a sport this build cannot name', () => {
    expect(toHome(home(null)).ranking).toBeUndefined();
    expect(toHome(home()).ranking).toBeUndefined();
    expect(
      toHome(home({ sport: 'CURLING' as Wire['Sport'], general_place: 3, friends_place: null }))
        .ranking,
    ).toBeUndefined();
  });
});
