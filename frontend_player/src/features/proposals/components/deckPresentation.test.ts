/**
 * The sentences the Games deck composes from a value — the lines the router suite does not reach
 * one by one: the cap's three weeks, the countdown's two forms, the sides as a line and as the bar,
 * a counted phrase at one, the refusals, and a game's details.
 */

import { AppError } from '@/shared/errors';

import { rowsOf, type DeckCard, type DeckPerson } from '../domain/deck';

import {
  answersByWords,
  barLabels,
  capLine,
  countdownWords,
  detailsShareWords,
  fillingStatus,
  gameDayWords,
  inOnGameLine,
  refusalMessage,
  ribbonWords,
  segmentLabel,
  shareAside,
  sidesSpoken,
  stampsFor,
  tileLabel,
  vsLine,
} from './deckPresentation';

function person(name: string, extra: Partial<DeckPerson> = {}): DeckPerson {
  return { playerId: name, isYou: false, name, level: 2.7, isIn: false, ...extra };
}

const YOU = person('Ada Lovelace', { isYou: true, level: 2.71 });

const SIDES: Pick<DeckCard, 'sides'> = {
  sides: {
    yours: [YOU, person('Zofia Bielecka', { isIn: true })],
    theirs: [person('Karol Tomaszewski', { isIn: true }), person('Ania Kowalska', { isIn: true })],
  },
};

describe('the lines above the deck', () => {
  it('names a segment with its count', () => {
    expect(segmentLabel('competitive', 7)).toBe('Competitive · 7');
    expect(segmentLabel('forFun', 1)).toBe('For fun · 1');
  });

  it('says which weeks are full, counting one game as one', () => {
    expect(capLine({ weeks: 'this', booked: 2 })).toBe(
      'Your 2 games this week are booked — showing next week',
    );
    expect(capLine({ weeks: 'next', booked: 1 })).toBe(
      'Your 1 game next week is booked — showing this week',
    );
    expect(capLine({ weeks: 'both', booked: 3 })).toBe(
      'Your 3 games this week and next are booked',
    );
  });
});

describe('the ribbon', () => {
  it('names the challenger whole, and the group when nobody can be named', () => {
    expect(ribbonWords({ kind: 'challenge', by: 'Kuba Wiśniewski' })).toBe(
      'Kuba Wiśniewski challenged you',
    );
    expect(ribbonWords({ kind: 'challenge' })).toBe('The group challenged you');
  });

  it('counts down in hours and padded minutes, then minutes, and draws nothing a day away', () => {
    expect(countdownWords({ kind: 'hours', hours: 21, minutes: 0 })).toBe('21 h 00');
    expect(countdownWords({ kind: 'hours', hours: 3, minutes: 7 })).toBe('3 h 07');
    expect(countdownWords({ kind: 'minutes', minutes: 45 })).toBe('45 min');
    expect(countdownWords({ kind: 'far' })).toBeUndefined();
  });
});

describe('the sides', () => {
  const { top, bottom } = rowsOf(SIDES, 2);

  it('draws stems in the vs line, the top row first', () => {
    expect(vsLine(top, bottom)).toBe('Karol + Ania vs Zofia + You');
  });

  it('says the sides whole', () => {
    expect(sidesSpoken(top, bottom)).toBe(
      'Karol Tomaszewski and Ania Kowalska against Zofia Bielecka and you',
    );
  });

  it('labels the bar with your side on the left, you first', () => {
    expect(barLabels([top, bottom])).toEqual(['You + Zofia', 'Karol + Ania']);
  });

  it('says a tile’s person, their Level, and In', () => {
    expect(tileLabel(person('Karol Tomaszewski', { isIn: true, level: 2.75 }), false)).toBe(
      'Karol Tomaszewski, level 2,75, In',
    );
    expect(tileLabel(YOU, false)).toBe('You, level 2,71');
    expect(tileLabel(YOU, true)).toBe('You, you complete it');
  });

  it('counts one person In as one', () => {
    expect(inOnGameLine(1)).toBe('1 person is In on this game');
    expect(inOnGameLine(4)).toBe('4 people are In on this game');
  });
});

describe('the stamps', () => {
  const card = { shareGrosze: 3200 } as DeckCard;

  it('carry the share only when the yes charges at once', () => {
    expect(stampsFor(card, true)).toEqual({
      yes: { words: 'I’m in', figure: '32 zł' },
      no: { words: 'Not this time' },
    });
    expect(stampsFor(card, false).yes).toEqual({ words: 'I’m in' });
  });
});

describe('a refused answer', () => {
  const refusal = (code: string, details?: Readonly<Record<string, unknown>>) =>
    new AppError('conflict', 'business-conflict', 'refused', {
      code,
      status: 409,
      ...(details === undefined ? {} : { details }),
    });

  it('says the route’s code in words', () => {
    expect(refusalMessage(refusal('proposal_is_full'))).toBe('That game just filled.');
  });
});

describe('a game’s details', () => {
  it('says the status, the day and the money row', () => {
    expect(fillingStatus(2, 4)).toBe('Filling · 2 of 4 in');
    expect(gameDayWords({ kind: 'dated', weekday: 6, day: '2026-10-10' })).toBe('Saturday 10 Oct');
    // Friday 2 October, 13:00 in Warsaw.
    expect(shareAside('2026-10-02T11:00:00Z', 5)).toBe('if it fills · book by Fri 13:00');
  });

  /** Q98: when the club answers — the hour alone on the read's day, else the weekday with it. */
  it('says when the club answers, and under the share while the game waits for it', () => {
    // 11:00 on Wednesday 30 September, and 00:15 on Sunday 4 October, in Warsaw.
    const today = { at: '2026-09-30T09:00:00Z', today: true };
    const sunday = { at: '2026-10-03T22:15:00Z', today: false };
    expect(answersByWords('Kazimierz Padel', today)).toBe('Kazimierz Padel answers by 11:00');
    expect(answersByWords(undefined, sunday)).toBe('The club answers by Sun 00:15');

    const card = { deadline: '2026-10-02T11:00:00Z', club: { id: 'c-1', name: 'Kazimierz Padel' } };
    expect(detailsShareWords('WAITING_FOR_THE_CLUB', card, 5, today)).toEqual({
      below: 'Kazimierz Padel answers by 11:00 · Nobody pays until it confirms',
    });
    expect(detailsShareWords('WAITING_FOR_THE_CLUB', card, 5, undefined)).toEqual({
      below: 'Nobody pays until Kazimierz Padel confirms',
    });
    expect(detailsShareWords('FILLING', card, 5, undefined)).toEqual({
      aside: 'if it fills · book by Fri 13:00',
    });
    expect(detailsShareWords('FILLED', card, 5, undefined)).toEqual({});
  });

  /** Q111: one payment awaited — until when under the share; the payer reads their own time. */
  it('says under the share that the game waits for one payment, and the payer’s own time', () => {
    // 14:40 on Tuesday 6 October in Warsaw.
    const twentyToThree = { at: '2026-10-06T12:40:00Z', today: true };
    const card = { deadline: '2026-10-06T15:00:00Z', club: { id: 'c-1', name: 'Bonarka Arena' } };
    expect(
      detailsShareWords('WAITING_FOR_A_PAYMENT', card, 2, undefined, { dueBy: twentyToThree }),
    ).toEqual({ below: 'Waiting for one payment · until 14:40 · Nobody pays until it’s in' });
    expect(detailsShareWords('WAITING_FOR_A_PAYMENT', card, 2, undefined)).toEqual({
      below: 'Waiting for one payment · Nobody pays until it’s in',
    });
    expect(
      detailsShareWords('WAITING_FOR_A_PAYMENT', card, 2, undefined, {
        dueBy: twentyToThree,
        yoursBy: twentyToThree,
      }),
    ).toEqual({ below: 'Confirm your payment by 14:40' });
    // Gone back to filling while the payer's time runs on (#625): the book-by, and their time.
    expect(detailsShareWords('FILLING', card, 2, undefined, { yoursBy: twentyToThree })).toEqual({
      aside: 'if it fills · book by Tue 17:00',
      below: 'Confirm your payment by 14:40',
    });
  });
});
