/** What the moment a game fills says: the count, It's a game! spoken whole, and a share's facts. */

import {
  bookingAnnouncement,
  bookingIn,
  chargeGameLine,
  chargeLine,
  itsAGameLine,
  itsAGameSentence,
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
        club: 'Kazimierz Padel',
        answerBy: { at: '2026-09-30T19:15:00Z', today: true },
      }).drawn,
    ).toBe('Kazimierz Padel answers by 21:15 · Nobody pays until it confirms');
  });

  it('names the weekday when the deadline falls on another day', () => {
    expect(
      itsAGameLine({
        club: 'Kazimierz Padel',
        answerBy: { at: '2026-10-01T07:00:00Z', today: false },
      }).drawn,
    ).toBe('Kazimierz Padel answers by Thu 09:00 · Nobody pays until it confirms');
  });

  it('says only that nobody pays until it confirms, with no deadline to give', () => {
    expect(itsAGameLine({ club: 'Kazimierz Padel' })).toEqual({
      drawn: 'Nobody pays until Kazimierz Padel confirms',
      spoken: 'Nobody pays until Kazimierz Padel confirms',
    });
    expect(itsAGameLine({}).drawn).toBe('Nobody pays until the club confirms');
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
