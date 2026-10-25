/**
 * The sentences the Games deck composes from a value — the lines the router suite does not reach
 * one by one: the cap's three weeks, the countdown's two forms, the sides as a line and as the bar,
 * a counted phrase at one, the refusals, and a game's details.
 */

import { AppError } from '@/shared/errors';

import { rowsOf, type DeckCard, type DeckPerson } from '../domain/deck';

import {
  answerLabels,
  barLabels,
  capLine,
  countdownWords,
  courtLine,
  detailsShareWords,
  fillingStatus,
  gameDayWords,
  inOnGameLine,
  payLabel,
  paySpoken,
  refusalMessage,
  ribbonWords,
  segmentLabel,
  shareAside,
  sidesSpoken,
  stampsFor,
  tileLabel,
  vsLine,
  yesButtonLabel,
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

describe('the stamps (Q124)', () => {
  const card = { shareGrosze: 3200 } as DeckCard;

  it('say Pay with the share when the yes charges at once', () => {
    expect(stampsFor(card, true)).toEqual({
      yes: { words: 'Pay', figure: '32 zł' },
      no: { words: 'Not this time' },
    });
  });

  it('say I’m in with the share on a vote, so the word tells it from a payment', () => {
    expect(stampsFor(card, false)).toEqual({
      yes: { words: 'I’m in', figure: '32 zł' },
      no: { words: 'Not this time' },
    });
  });
});

describe('a button that moves money says Pay (Q124)', () => {
  it('draws the share, and says aloud whether it is held until the cut-off or paid now (Q113)', () => {
    expect(payLabel('27 zł')).toBe('Pay 27 zł');
    expect(paySpoken('27 zł', true)).toBe('Pay 27 zł, held until the cut-off');
    expect(paySpoken('27 zł', false)).toBe('Pay 27 zł, paid now');
  });

  it('is the yes on a game whose yes charges at once, and I’m in on a vote', () => {
    expect(yesButtonLabel(true, '32 zł')).toBe('Pay 32 zł');
    expect(yesButtonLabel(false, '32 zł')).toBe('I’m in');
  });

  it('leaves the deck’s ball I’m in — on a Seat open card saying what the share does, plainly on any other', () => {
    const rescue = { type: 'SEAT_OPEN', shareGrosze: 2700 } as const;
    expect(answerLabels({ ...rescue, noFreeCancellation: false })).toEqual({
      pass: 'Not this time',
      accept: 'I’m in, 27 zł held until the cut-off',
      record: 'Game details',
    });
    expect(answerLabels({ ...rescue, noFreeCancellation: true }).accept).toBe(
      'I’m in, 27 zł paid now',
    );
    expect(
      answerLabels({ type: 'PICKED_FOR_YOU', shareGrosze: 2700, noFreeCancellation: false }).accept,
    ).toBe('I’m in');
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

  it('says the book-by beside the share while the game fills, and nothing once it is over', () => {
    const card = { deadline: '2026-10-02T11:00:00Z' };
    expect(detailsShareWords('FILLING', card, 5)).toEqual({
      aside: 'if it fills · book by Fri 13:00',
    });
    for (const status of ['FILLED', 'EXPIRED', 'WITHDRAWN', 'COURT_HOUR_LOST'] as const) {
      expect(detailsShareWords(status, card, 5)).toEqual({});
    }
  });

  /** Q111: one payment awaited — until when under the share; the payer reads their own time. */
  it('says under the share that the game waits for one payment, and the payer’s own time', () => {
    // 14:40 on Tuesday 6 October in Warsaw.
    const twentyToThree = { at: '2026-10-06T12:40:00Z', today: true };
    const card = { deadline: '2026-10-06T15:00:00Z' };
    expect(detailsShareWords('WAITING_FOR_A_PAYMENT', card, 2, { dueBy: twentyToThree })).toEqual({
      below: 'Waiting for one payment · until 14:40 · Nobody pays until it’s in',
    });
    expect(detailsShareWords('WAITING_FOR_A_PAYMENT', card, 2)).toEqual({
      below: 'Waiting for one payment · Nobody pays until it’s in',
    });
    expect(
      detailsShareWords('WAITING_FOR_A_PAYMENT', card, 2, {
        dueBy: twentyToThree,
        yours: { by: twentyToThree, window: 'PAY' },
      }),
    ).toEqual({ below: 'Confirm your payment by 14:40' });
    // Before the cut-off it is their time to fix the card (#638; Q113).
    expect(
      detailsShareWords('WAITING_FOR_A_PAYMENT', card, 2, {
        dueBy: twentyToThree,
        yours: { by: twentyToThree, window: 'FIX_THE_CARD' },
      }),
    ).toEqual({ below: 'Fix your card by 14:40' });
    // Gone back to filling while the payer's time runs on (#625): the book-by, and their time.
    expect(
      detailsShareWords('FILLING', card, 2, {
        yours: { by: twentyToThree, window: 'UNNAMED' },
      }),
    ).toEqual({
      aside: 'if it fills · book by Tue 17:00',
      below: 'Confirm your payment by 14:40',
    });
  });
});

describe('the court block’s kind (#677)', () => {
  const card = { startsAt: '2026-10-03T14:00:00Z', club: { id: 'club-1', name: 'Ogrody 33' } };

  it('says Indoor or Outdoor on a card, where the server says which', () => {
    expect(courtLine(undefined, { ...card, indoor: true })).toBe('16:00 · Ogrody 33 · Indoor');
    expect(courtLine(undefined, { ...card, indoor: false })).toBe('16:00 · Ogrody 33 · Outdoor');
  });

  it('says nothing about the kind where the server says nothing (mixed courts)', () => {
    expect(courtLine(undefined, card)).toBe('16:00 · Ogrody 33');
  });

  it('follows a booked court’s number in lower case: Court 6 · indoor', () => {
    expect(courtLine(undefined, { ...card, courtName: 'Court 6', indoor: true })).toBe(
      '16:00 · Ogrody 33 · Court 6 · indoor',
    );
  });
});
