import { AppError } from '@/shared/errors';
import { setDeviceZone } from '@/test-support/deviceZone';

import {
  acceptLabel,
  answerRefusal,
  coverLine,
  friendsGamesHeading,
  gameOf,
  invitationClock,
  invitationLine,
  payModeWords,
  seatStateWords,
  seatsLineWords,
  sendLabel,
  sendRefusal,
} from './friendsGamePresentation';

/** Thursday 1 October 2026, 10:00 in Warsaw. */
const NOW = Date.parse('2026-10-01T08:00:00Z');
/** Saturday 3 October, 10:00 in Warsaw. */
const SATURDAY_10 = '2026-10-03T08:00:00Z';
/** Friday 2 October, 10:00 — the club's cut-off. */
const CUT_OFF = '2026-10-02T08:00:00Z';

beforeAll(() => setDeviceZone('Europe/Warsaw'));

function refused(code: string, details?: Record<string, unknown>): AppError {
  return new AppError('conflict', 'business-conflict', 'refused', {
    code,
    status: 409,
    ...(details === undefined ? {} : { details }),
  });
}

describe('the send sheet (the words §29.7)', () => {
  it('names what the order charges', () => {
    expect(sendLabel(2500)).toBe('Send game and pay 25 zł');
    expect(sendLabel(10000)).toBe('Send game and pay 100 zł');
  });

  it('holds the court until the cut-off, a seat each in doubles, the other seat in singles', () => {
    expect(
      coverLine({ priceGrosze: 10000, shareGrosze: 2500, cutOff: CUT_OFF, singles: false }),
    ).toBe(
      'We hold 100 zł on your card until Fri 10:00. You pay 25 zł, plus 25 zł for any seat still empty then.',
    );
    expect(
      coverLine({ priceGrosze: 5000, shareGrosze: 2500, cutOff: CUT_OFF, singles: true }),
    ).toBe(
      'We hold 50 zł on your card until Fri 10:00. You pay 25 zł, plus 25 zł if the other seat is still empty then.',
    );
    expect(
      coverLine({ priceGrosze: 10000, shareGrosze: 2500, cutOff: undefined, singles: false }),
    ).toMatch(/^We hold 100 zł on your card until the club’s cut-off\./);
  });

  it('says each refusal with the sender’s own numbers', () => {
    expect(sendRefusal(refused('friends_games_waiting', { cap: 2 }), SATURDAY_10)).toBe(
      'You have 2 friends games waiting for answers. Send this one once one of them is settled.',
    );
    expect(sendRefusal(refused('you_play_then'), SATURDAY_10)).toBe(
      'You already have a game at 10:00.',
    );
    expect(sendRefusal(refused('games_per_week_booked'), SATURDAY_10)).toBe(
      'Your week is full, the most you set in Games & money.',
    );
    expect(sendRefusal(refused('court_just_taken'), SATURDAY_10)).toBe(
      'That court was just booked by another game. Nothing was charged — try again.',
    );
  });
});

describe('the invitation (the words §29.8)', () => {
  it('heads the row and names whose game', () => {
    expect(friendsGamesHeading(2)).toBe('Friends game · 2');
    expect(gameOf('tomek.k')).toBe('tomek.k’s game');
    expect(gameOf(undefined)).toBe('A friend’s game');
  });

  it('counts the time left down as the deck’s ribbon does, coral under an hour', () => {
    expect(invitationClock('2026-10-01T09:35:00Z', NOW)).toEqual({
      words: '1 h 35',
      spoken: '1 hour 35 minutes left to answer',
      urgent: false,
    });
    expect(invitationClock('2026-10-01T08:45:00Z', NOW)).toEqual(
      expect.objectContaining({ words: '45 min', urgent: true }),
    );
    expect(invitationClock('2026-10-01T07:00:00Z', NOW)).toBeUndefined();
    expect(invitationClock(undefined, NOW)).toBeUndefined();
  });

  it('writes the game’s line with its kind', () => {
    expect(
      invitationLine(
        {
          startsAt: SATURDAY_10,
          club: { id: 'c', name: 'Ogrody 33' },
          courtName: 'Court 3',
          sport: 'padel',
          kind: 'forFun',
        },
        NOW,
      ),
    ).toBe('Saturday 10:00 · Ogrody 33 · Court 3 · Padel · For fun');
  });

  it('names the answer by the pay mode', () => {
    expect(acceptLabel({ payMode: 'SPLIT_THE_COST' }, 2500)).toBe('Accept and pay 25 zł');
    expect(acceptLabel({ payMode: 'WHOLE_COURT' }, 2500)).toBe('Accept');
  });

  it('says a full week, singular and plural, and an hour taken', () => {
    expect(
      answerRefusal(refused('games_per_week_booked', { games_per_week: 1 }), SATURDAY_10),
    ).toBe('Your week is full: 1 game, the most you set in Games & money.');
    expect(
      answerRefusal(refused('games_per_week_booked', { games_per_week: 4 }), SATURDAY_10),
    ).toBe('Your week is full: 4 games, the most you set in Games & money.');
    expect(answerRefusal(refused('invitation_not_waiting'), SATURDAY_10)).toBe(
      'That invitation has ended.',
    );
  });
});

describe('the sender’s game and the details', () => {
  it('says who is in and who it waits for, each form of §29.8', () => {
    expect(
      seatsLineWords({ friendsIn: 2, friendsSeated: 3, waitingFor: ['ania.k'], empty: 0 }),
    ).toBe('2 of 3 friends in · waiting for ania.k');
    expect(
      seatsLineWords({ friendsIn: 0, friendsSeated: 3, waitingFor: ['ewa.m', 'ania.k'], empty: 1 }),
    ).toBe('Waiting for ewa.m and ania.k · 1 seat empty');
    expect(seatsLineWords({ friendsIn: 1, friendsSeated: 3, waitingFor: [], empty: 2 })).toBe(
      '1 of 3 friends in · 2 seats empty',
    );
    expect(
      seatsLineWords({ friendsIn: 0, friendsSeated: 1, waitingFor: ['ania.k'], empty: 0 }),
    ).toBe('Waiting for ania.k');
  });

  it('words each seat’s state', () => {
    expect(seatStateWords({ state: 'IN' }, NOW)).toBe('In');
    expect(seatStateWords({ state: 'WAITING', waitingUntil: '2026-10-02T05:00:00Z' }, NOW)).toBe(
      'waiting · 21 h 00 left',
    );
    expect(seatStateWords({ state: 'CANT_MAKE_IT' }, NOW)).toBe('can’t make it');
    expect(seatStateWords({ state: 'DIDNT_ANSWER' }, NOW)).toBe('didn’t answer');
    expect(seatStateWords({ state: 'EMPTY' }, NOW)).toBe('empty');
  });

  it('reads the pay mode', () => {
    expect(payModeWords({ payMode: 'SPLIT_THE_COST', senderNickname: 'tomek.k' })).toBe('Split');
    expect(payModeWords({ payMode: 'WHOLE_COURT', senderNickname: 'tomek.k' })).toBe(
      'tomek.k paid the court',
    );
  });
});
