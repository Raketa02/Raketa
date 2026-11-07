import type { DeckCard, DeckPerson } from './deck';
import {
  acceptPaymentOf,
  answerRefusalOf,
  courtPrice,
  gamesPerWeekOf,
  invitationFaces,
  invitationWaits,
  seatStateAt,
  seatsCanRunOut,
  seatsLineOf,
  seatsShown,
  sendCharge,
  sendPaymentsOf,
  sendRefusalOf,
  anySeatToOpen,
  seatActionsAt,
  seatToInviteOf,
  seatWriteRefusalOf,
  twoWayLeaveIn,
  waitingCapOf,
  type FriendsGame,
  type SeatShown,
} from './friendsGame';

const NOW = Date.parse('2026-10-01T08:00:00Z');
const LATER = '2026-10-01T20:00:00Z';
const EARLIER = '2026-10-01T07:00:00Z';

const person = (playerId: string, name: string, isYou = false): DeckPerson => ({
  playerId,
  name,
  isYou,
  isIn: false,
});

const SIDES: DeckCard['sides'] = {
  yours: [person('tomek', 'tomek.k', true), person('ewa', 'ewa.m')],
  theirs: [person('magda', 'magda.p'), person('ania', 'ania.k')],
};

const game = (extra: Partial<FriendsGame> = {}): FriendsGame => ({
  senderId: 'tomek',
  senderNickname: 'tomek.k',
  youAreTheSender: true,
  payMode: 'SPLIT_THE_COST',
  seats: [
    { playerId: 'tomek', state: 'IN' },
    { playerId: 'ewa', state: 'IN' },
    { playerId: 'magda', state: 'IN' },
    { playerId: 'ania', state: 'WAITING', waitingUntil: LATER },
  ],
  friendsIn: 2,
  friendsSeated: 3,
  canCallOff: true,
  ...extra,
});

describe('seatStateAt', () => {
  it('reads a waiting seat as waiting while its time runs, and didn’t answer once it is over', () => {
    expect(seatStateAt({ playerId: 'a', state: 'WAITING', waitingUntil: LATER }, NOW)).toBe(
      'WAITING',
    );
    expect(seatStateAt({ playerId: 'a', state: 'WAITING', waitingUntil: EARLIER }, NOW)).toBe(
      'DIDNT_ANSWER',
    );
  });

  it('keeps every other state as read', () => {
    expect(seatStateAt({ playerId: 'a', state: 'CANT_MAKE_IT' }, NOW)).toBe('CANT_MAKE_IT');
    expect(seatStateAt({ playerId: 'a', state: 'IN' }, NOW)).toBe('IN');
  });
});

describe('invitationWaits', () => {
  it('is true only while the reader’s own time runs', () => {
    expect(invitationWaits({ yourInvitationUntil: LATER }, NOW)).toBe(true);
    expect(invitationWaits({ yourInvitationUntil: EARLIER }, NOW)).toBe(false);
    expect(invitationWaits({}, NOW)).toBe(false);
  });
});

describe('seatsCanRunOut', () => {
  it('ticks while a seat waits or the reader’s invitation does', () => {
    expect(seatsCanRunOut(game())).toBe(true);
    expect(seatsCanRunOut(game({ seats: [{ playerId: 'tomek', state: 'IN' }] }))).toBe(false);
    expect(seatsCanRunOut(game({ seats: [], yourInvitationUntil: LATER }))).toBe(true);
  });
});

describe('seatsLineOf', () => {
  it('says how many friends are in and who the sender’s game waits for', () => {
    expect(seatsLineOf({ friendsGame: game(), sides: SIDES }, NOW)).toEqual({
      friendsIn: 2,
      friendsSeated: 3,
      waitingFor: [SIDES.theirs[1]],
      empty: 0,
    });
  });

  it('counts a no, a silence and a seat left as empty — and a waiting seat run out', () => {
    const line = seatsLineOf(
      {
        friendsGame: game({
          seats: [
            { playerId: 'tomek', state: 'IN' },
            { playerId: 'ewa', state: 'CANT_MAKE_IT' },
            { playerId: 'magda', state: 'EMPTY' },
            { playerId: 'ania', state: 'WAITING', waitingUntil: EARLIER },
          ],
          friendsIn: 0,
        }),
        sides: SIDES,
      },
      NOW,
    );
    expect(line).toEqual({ friendsIn: 0, friendsSeated: 3, waitingFor: [], empty: 3 });
  });

  it('is nothing once every seat is In, for a friend’s own card, and for a game a fill booked', () => {
    const allIn = game({
      seats: game().seats.map((seat) => ({ playerId: seat.playerId, state: 'IN' as const })),
    });
    expect(seatsLineOf({ friendsGame: allIn, sides: SIDES }, NOW)).toBeUndefined();
    expect(
      seatsLineOf({ friendsGame: game({ youAreTheSender: false }), sides: SIDES }, NOW),
    ).toBeUndefined();
    expect(seatsLineOf({ sides: SIDES }, NOW)).toBeUndefined();
  });

  it('passes a seat the court does not draw on unnamed', () => {
    const line = seatsLineOf(
      {
        friendsGame: game({
          seats: [
            { playerId: 'tomek', state: 'IN' },
            { playerId: 'ghost', state: 'WAITING', waitingUntil: LATER },
          ],
          friendsSeated: 1,
        }),
        sides: SIDES,
      },
      NOW,
    );
    expect(line?.waitingFor).toEqual([{ playerId: 'ghost', isYou: false, isIn: false }]);
  });
});

describe('seatsShown', () => {
  it('lists every seat in the read’s order with its person and its state now', () => {
    const shown = seatsShown({ friendsGame: game(), sides: SIDES }, NOW);
    expect(shown.map((seat) => [seat.person.playerId, seat.state])).toEqual([
      ['tomek', 'IN'],
      ['ewa', 'IN'],
      ['magda', 'IN'],
      ['ania', 'WAITING'],
    ]);
    expect(shown[3]?.waitingUntil).toBe(LATER);
  });

  it('is empty for a game a fill booked', () => {
    expect(seatsShown({ sides: SIDES }, NOW)).toEqual([]);
  });

  it('carries an empty seat’s name, what the reader may do, and the invitations still waiting now', () => {
    const shown = seatsShown(
      {
        friendsGame: game({
          seats: [
            { playerId: 'tomek', state: 'IN' },
            {
              playerId: 'ania',
              state: 'CANT_MAKE_IT',
              seatOf: 'ania',
              canInvite: true,
              canOpen: true,
              invitations: [
                { playerId: 'piotr', nickname: 'piotr.s', until: LATER },
                { playerId: 'kuba', nickname: 'kuba.w', until: EARLIER },
              ],
            },
          ],
        }),
        sides: SIDES,
      },
      NOW,
    );

    expect(shown[1]).toMatchObject({
      seatOf: 'ania',
      canInvite: true,
      canOpen: true,
      invitations: [{ playerId: 'piotr', nickname: 'piotr.s', until: LATER }],
    });
    expect(shown[0]).toMatchObject({ canInvite: false, canOpen: false, invitations: [] });
    expect(shown[0]?.seatOf).toBeUndefined();
  });
});

describe('seatActionsAt', () => {
  const CUT_OFF = '2026-10-02T08:00:00Z';
  const STARTS = '2026-10-03T08:00:00Z';
  const seat = (extra: Partial<SeatShown> = {}): SeatShown => ({
    person: person('ania', 'ania.k'),
    state: 'CANT_MAKE_IT',
    seatOf: 'ania',
    invitations: [],
    canInvite: true,
    canOpen: true,
    ...extra,
  });

  it('offers the sender both on an empty seat before the cut-off', () => {
    expect(seatActionsAt(seat(), { now: NOW, cutOff: CUT_OFF, startsAt: STARTS })).toEqual({
      invite: true,
      open: true,
    });
  });

  it('offers a friend In only Invite a friend — Open is the sender’s', () => {
    expect(
      seatActionsAt(seat({ canOpen: false }), { now: NOW, cutOff: CUT_OFF, startsAt: STARTS }),
    ).toEqual({ invite: true, open: false });
  });

  it('takes Open away at the cut-off on the read’s clock, and Invite at the start', () => {
    const afterCutOff = Date.parse(CUT_OFF);
    expect(seatActionsAt(seat(), { now: afterCutOff, cutOff: CUT_OFF, startsAt: STARTS })).toEqual({
      invite: true,
      open: false,
    });
    expect(
      seatActionsAt(seat(), { now: Date.parse(STARTS), cutOff: CUT_OFF, startsAt: STARTS }),
    ).toEqual({ invite: false, open: false });
    expect(seatActionsAt(seat(), { now: NOW, cutOff: undefined, startsAt: STARTS }).open).toBe(
      false,
    );
  });

  it('opens no seat already open, and offers nothing on a seat the read does not name', () => {
    expect(
      seatActionsAt(seat({ state: 'SEAT_OPEN' }), {
        now: NOW,
        cutOff: CUT_OFF,
        startsAt: STARTS,
      }),
    ).toEqual({ invite: true, open: false });
    const unnamed: SeatShown = { ...seat(), seatOf: undefined };
    expect(seatActionsAt(unnamed, { now: NOW, cutOff: CUT_OFF, startsAt: STARTS })).toEqual({
      invite: false,
      open: false,
    });
  });

  it('offers nothing on a seat somebody holds or is still held for', () => {
    for (const state of ['IN', 'WAITING'] as const) {
      expect(
        seatActionsAt(seat({ state }), { now: NOW, cutOff: CUT_OFF, startsAt: STARTS }),
      ).toEqual({ invite: false, open: false });
    }
  });
});

describe('anySeatToOpen', () => {
  it('is true while the read lets the reader open some seat — the group’s name is then read', () => {
    const empty = { playerId: 'ania', state: 'CANT_MAKE_IT', seatOf: 'ania' } as const;
    expect(anySeatToOpen({ friendsGame: game({ seats: [{ ...empty, canOpen: true }] }) })).toBe(
      true,
    );
    expect(anySeatToOpen({ friendsGame: game({ seats: [empty] }) })).toBe(false);
    expect(anySeatToOpen({})).toBe(false);
  });
});

describe('seatToInviteOf', () => {
  it('names the game’s group, sport and hour, and everybody the picker leaves out', () => {
    const seat = seatToInviteOf(
      {
        bookingId: 'b-1',
        groupId: 'g-1',
        sport: 'padel',
        startsAt: '2026-10-03T08:00:00Z',
        sides: SIDES,
        friendsGame: game({
          seats: [
            { playerId: 'tomek', state: 'IN' },
            { playerId: 'ewa', state: 'IN' },
            { playerId: 'magda', state: 'IN' },
            {
              playerId: 'bartek',
              state: 'CANT_MAKE_IT',
              seatOf: 'bartek',
              invitations: [{ playerId: 'piotr', until: LATER }],
            },
          ],
        }),
      },
      'bartek',
    );

    expect(seat).toEqual({
      bookingId: 'b-1',
      seatOf: 'bartek',
      groupId: 'g-1',
      sport: 'padel',
      startsAt: '2026-10-03T08:00:00Z',
      onTheGame: ['tomek', 'ewa', 'magda', 'ania', 'bartek', 'piotr'],
    });
  });
});

describe('twoWayLeaveIn', () => {
  it('is the pay mode — two ways to leave — for the sender before the cut-off', () => {
    expect(twoWayLeaveIn({ friendsGame: game() }, 'BEFORE_THE_CUT_OFF')).toBe('SPLIT_THE_COST');
    expect(
      twoWayLeaveIn({ friendsGame: game({ payMode: 'WHOLE_COURT' }) }, 'BEFORE_THE_CUT_OFF'),
    ).toBe('WHOLE_COURT');
  });

  it('is nothing after the cut-off, for a friend, for a game a fill booked, and without Call it off', () => {
    expect(twoWayLeaveIn({ friendsGame: game() }, 'AFTER_THE_CUT_OFF')).toBeUndefined();
    expect(twoWayLeaveIn({ friendsGame: game() }, undefined)).toBeUndefined();
    expect(
      twoWayLeaveIn({ friendsGame: game({ youAreTheSender: false }) }, 'BEFORE_THE_CUT_OFF'),
    ).toBeUndefined();
    expect(twoWayLeaveIn({}, 'BEFORE_THE_CUT_OFF')).toBeUndefined();
    expect(
      twoWayLeaveIn({ friendsGame: game({ canCallOff: false }) }, 'BEFORE_THE_CUT_OFF'),
    ).toBeUndefined();
  });
});

describe('invitationFaces', () => {
  it('puts the reader last, ticks those In and fades the others still to answer', () => {
    const invitation = {
      sides: {
        yours: [person('ewa', 'ewa.m', true), person('tomek', 'tomek.k')],
        theirs: [person('magda', 'magda.p'), person('ania', 'ania.k')],
      },
      friendsGame: game({
        youAreTheSender: false,
        seats: [
          { playerId: 'tomek', state: 'IN' },
          { playerId: 'ewa', state: 'WAITING', waitingUntil: LATER },
          { playerId: 'magda', state: 'IN' },
          { playerId: 'ania', state: 'WAITING', waitingUntil: LATER },
        ],
      }),
    };
    expect(
      invitationFaces(invitation, NOW).map((face) => [face.person.playerId, face.isIn, face.faded]),
    ).toEqual([
      ['tomek', true, false],
      ['magda', true, false],
      ['ania', false, true],
      ['ewa', false, false],
    ]);
  });
});

describe('the money', () => {
  it('prices the court at every seat’s share', () => {
    expect(courtPrice(2500, 4)).toBe(10000);
    expect(courtPrice(2500, 2)).toBe(5000);
  });

  it('charges the sender their share with Split and the court with Whole court', () => {
    expect(sendCharge('SPLIT_THE_COST', 2500, 4)).toBe(2500);
    expect(sendCharge('WHOLE_COURT', 2500, 4)).toBe(10000);
  });
});

describe('sendPaymentsOf', () => {
  const refused = (seatChargeId: string, refusal: 'AUTHENTICATION_REQUIRED' | 'DECLINED') => ({
    seatChargeId,
    refusal,
  });

  it('confirms every payment the bank refused, one after another', () => {
    expect(
      sendPaymentsOf([refused('a', 'AUTHENTICATION_REQUIRED'), refused('b', 'DECLINED')]),
    ).toEqual({
      kind: 'confirm',
      payments: [refused('a', 'AUTHENTICATION_REQUIRED'), refused('b', 'DECLINED')],
    });
  });

  it('asks for a method first, then the terms, before any confirmation', () => {
    expect(
      sendPaymentsOf([
        refused('a', 'AUTHENTICATION_REQUIRED'),
        { seatChargeId: 'b', refusal: 'NO_METHOD' },
      ]),
    ).toEqual({ kind: 'setUp' });
    expect(sendPaymentsOf([{ seatChargeId: 'b', refusal: 'TERMS_NEEDED' }])).toEqual({
      kind: 'termsAgain',
    });
  });

  it('sends again when nothing is named', () => {
    expect(sendPaymentsOf([])).toEqual({ kind: 'sendAgain' });
  });
});

describe('sendRefusalOf', () => {
  it.each([
    ['payment_method_required', 'setUp'],
    ['court_just_taken', 'reread'],
    ['not_a_friend', 'reread'],
    ['no_level', 'reread'],
    ['cannot_play_together', 'reread'],
    ['court_hour_not_for_sale', 'courtGone'],
    ['friends_games_waiting', 'say'],
    ['you_play_then', 'say'],
    ['games_per_week_booked', 'say'],
    [undefined, 'say'],
  ] as const)('%s → %s', (code, refusal) => {
    expect(sendRefusalOf(code)).toBe(refusal);
  });
});

describe('answerRefusalOf', () => {
  it.each([
    ['payment_method_required', 'setUp'],
    ['invitation_not_waiting', 'gone'],
    ['booking_is_called_off', 'gone'],
    ['game_has_started', 'gone'],
    ['booking_not_found', 'gone'],
    ['you_play_then', 'say'],
    ['games_per_week_booked', 'say'],
  ] as const)('%s → %s', (code, refusal) => {
    expect(answerRefusalOf(code)).toBe(refusal);
  });
});

describe('seatWriteRefusalOf', () => {
  it.each([
    ['seat_just_taken', 'gone'],
    ['booking_is_called_off', 'gone'],
    ['game_has_started', 'gone'],
    ['booking_not_found', 'gone'],
    ['cut_off_has_passed', 'gone'],
    ['already_on_the_game', 'say'],
    ['not_a_friend', 'say'],
    ['no_level', 'say'],
    ['cannot_play_together', 'say'],
    ['friend_plays_then', 'say'],
    ['friends_week_is_full', 'say'],
    [undefined, 'say'],
  ] as const)('%s → %s', (code, refusal) => {
    expect(seatWriteRefusalOf(code)).toBe(refusal);
  });
});

describe('acceptPaymentOf', () => {
  it.each([
    ['AUTHENTICATION_REQUIRED', 'confirm'],
    ['DECLINED', 'confirm'],
    ['NO_METHOD', 'setUp'],
    ['TERMS_NEEDED', 'termsAgain'],
  ] as const)('%s → %s', (refusal, next) => {
    expect(acceptPaymentOf({ refusal })).toBe(next);
  });
});

describe('the numbers a refusal names', () => {
  it('reads the week’s games and the waiting cap, or nothing and the mechanics’ 2', () => {
    expect(gamesPerWeekOf({ games_per_week: 3 })).toBe(3);
    expect(gamesPerWeekOf({ games_per_week: 'three' })).toBeUndefined();
    expect(gamesPerWeekOf(undefined)).toBeUndefined();
    expect(waitingCapOf({ cap: 2 })).toBe(2);
    expect(waitingCapOf(undefined)).toBe(2);
  });
});
