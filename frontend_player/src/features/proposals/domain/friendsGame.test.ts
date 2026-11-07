import type { DeckCard, DeckPerson } from './deck';
import {
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
  waitingCapOf,
  type FriendsGame,
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
      waitingFor: ['ania.k'],
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

  it('names a seat the court cannot name as somebody', () => {
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
    expect(line?.waitingFor).toEqual(['Somebody']);
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

describe('the numbers a refusal names', () => {
  it('reads the week’s games and the waiting cap, or nothing and the mechanics’ 2', () => {
    expect(gamesPerWeekOf({ games_per_week: 3 })).toBe(3);
    expect(gamesPerWeekOf({ games_per_week: 'three' })).toBeUndefined();
    expect(gamesPerWeekOf(undefined)).toBeUndefined();
    expect(waitingCapOf({ cap: 2 })).toBe(2);
    expect(waitingCapOf(undefined)).toBe(2);
  });
});
