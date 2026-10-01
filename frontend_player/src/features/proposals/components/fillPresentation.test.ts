/** What the moment a game fills says: the count, It's a game! spoken whole, and a share's facts. */

import {
  bookingAnnouncement,
  bookingIn,
  chargeGameLine,
  chargeLine,
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
