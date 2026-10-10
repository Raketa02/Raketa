/** What the moment a game fills says: the count, It's a game! spoken whole, and a share's facts. */

import {
  bookingAnnouncement,
  bookingIn,
  chargeGameLine,
  chargeLine,
  itsAGameLine,
  itsAGameSentence,
  keepYourSeatBy,
  toConfirmRowLine,
} from './fillPresentation';

describe('the Undo toast', () => {
  it('counts in whole seconds, and says once that the booking can be undone', () => {
    expect(bookingIn(10)).toBe('Booking in 10 s');
    expect(bookingAnnouncement(10)).toBe('Booking in 10 seconds. You can undo it.');
  });
});

describe('It’s a game! as a listener hears it', () => {
  it('names you, your partner and the other side, whole', () => {
    expect(
      itsAGameSentence({
        yours: [
          { playerId: 'me', name: 'Ada Lovelace' },
          { playerId: 'z', name: 'Zofia Bielecka' },
        ],
        theirs: [
          { playerId: 'a', name: 'Ania Kowalska' },
          { playerId: 'e', name: 'Ewa Majewska' },
        ],
      }),
    ).toBe('It’s a game! You and Zofia Bielecka against Ania Kowalska and Ewa Majewska');
  });

  it('says singles as you against them, and a person with no name as the unknown mark', () => {
    expect(itsAGameSentence({ yours: [{ playerId: 'me' }], theirs: [{ playerId: 'gone' }] })).toBe(
      'It’s a game! You against ?',
    );
  });

  it('says the line under the word after the picture, a sentence a clause (Q103)', () => {
    const line = itsAGameLine({
      of: 'theClub',
      club: 'Kazimierz Padel',
      answerBy: { at: '2026-09-30T19:15:00Z', today: true },
    });
    expect(
      itsAGameSentence(
        { yours: [{ playerId: 'me' }], theirs: [{ playerId: 'k', name: 'Kuba Wiśniewski' }] },
        line.spoken,
      ),
    ).toBe(
      'It’s a game! You against Kuba Wiśniewski. Kazimierz Padel answers by 21:15. Nobody pays until it confirms',
    );
  });
});

/** Wednesday 30 September 2026 in Warsaw. */
describe('It’s a game!’s line at a club that confirms (Q103)', () => {
  it('says when the club answers — the hour alone that day, as Home writes it', () => {
    expect(
      itsAGameLine({
        of: 'theClub',
        club: 'Kazimierz Padel',
        answerBy: { at: '2026-09-30T19:15:00Z', today: true },
      }).drawn,
    ).toBe('Kazimierz Padel answers by 21:15 · Nobody pays until it confirms');
  });

  it('names the weekday when the deadline falls on another day', () => {
    expect(
      itsAGameLine({
        of: 'theClub',
        club: 'Kazimierz Padel',
        answerBy: { at: '2026-10-01T07:00:00Z', today: false },
      }).drawn,
    ).toBe('Kazimierz Padel answers by Thu 09:00 · Nobody pays until it confirms');
  });

  it('says only that nobody pays until it confirms, with no deadline to give', () => {
    expect(itsAGameLine({ of: 'theClub', club: 'Kazimierz Padel' })).toEqual({
      drawn: 'Nobody pays until Kazimierz Padel confirms',
      spoken: 'Nobody pays until Kazimierz Padel confirms',
    });
    expect(itsAGameLine({ of: 'theClub' }).drawn).toBe('Nobody pays until the club confirms');
  });
});

/** Tuesday 6 October 2026 in Warsaw. */
describe('It’s a game!’s line while one payment is missing (Q110)', () => {
  it('says until when, the hour alone that day, and never whose — drawn with dots, spoken in sentences', () => {
    expect(
      itsAGameLine({ of: 'aPayment', until: { at: '2026-10-06T12:40:00Z', today: true } }),
    ).toEqual({
      drawn: 'Waiting for one payment · until 14:40 · Nobody pays until it’s in',
      spoken: 'Waiting for one payment until 14:40. Nobody pays until it’s in',
    });
  });

  it('names the weekday when the time falls on another day', () => {
    expect(
      itsAGameLine({ of: 'aPayment', until: { at: '2026-10-06T22:15:00Z', today: false } }).drawn,
    ).toBe('Waiting for one payment · until Wed 00:15 · Nobody pays until it’s in');
  });
});

describe('the time to pay, where the payer confirms (Q109)', () => {
  it('names the time on the sheet, and on a To confirm row while it runs', () => {
    const by = { at: '2026-10-06T12:40:00Z', today: true } as const;
    expect(keepYourSeatBy(by)).toBe('Confirm your payment by 14:40 to keep your seat');
    expect(toConfirmRowLine(by)).toBe('Confirm your payment by 14:40');
  });

  it('says the seat is open to others on a row whose time ran out', () => {
    expect(toConfirmRowLine(undefined)).toBe(
      'Your seat stays open until you confirm — or someone else takes it.',
    );
  });
});

describe('a payment to confirm', () => {
  it('says the share and the seller, and the game it is for', () => {
    expect(chargeLine(3200, 'Bonarka Arena')).toBe('32 zł to Bonarka Arena');
    expect(chargeLine(2750, undefined)).toBe('27,50 zł to the club');
    // Wednesday 30 September 2026, 10:00 in Warsaw; the game Saturday 16:00.
    expect(
      chargeGameLine('padel', '2026-10-03T14:00:00Z', Date.parse('2026-09-30T08:00:00Z')),
    ).toBe('Padel · Saturday · 16:00');
  });
});
