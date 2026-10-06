/**
 * What a court's seats are called to a listener — the summary first, then each seat by its side
 * and role, never by an index (the-words §20.4). The group page's Friends court and its Games
 * card say these, and so did Play's builder, whose sentences they were until #574.
 */

import { SEAT_PLACES } from './seatPlace';
import { PLACE_CLAUSE, courtSummaryLabel, seatLabel } from './seatPlacePresentation';

describe("a court's summary", () => {
  it('says the sport and how full the court is, before any seat', () => {
    expect(courtSummaryLabel({ sportName: 'Padel', filled: 3, seats: 4 })).toBe(
      'Padel, 3 of 4 seats filled.',
    );
    expect(courtSummaryLabel({ sportName: 'Tennis', filled: 1, seats: 2 })).toBe(
      'Tennis, 1 of 2 seats filled.',
    );
  });
});

describe("a seat's name", () => {
  it('says who is where without a number for a person', () => {
    expect(seatLabel('YOUR_SIDE', { kind: 'you' })).toBe('Your side, you');
    expect(seatLabel('YOUR_PARTNER', { kind: 'player', name: 'Marek', level: 2.92 })).toBe(
      'Your side, your partner, Marek, level 2,92',
    );
    expect(seatLabel('THEIR_SIDE', { kind: 'player', name: 'Ana', level: 3.1 })).toBe(
      'Their side, Ana, level 3,10',
    );
    expect(seatLabel('THEIR_SIDE', { kind: 'empty' })).toBe('Their side, empty');
  });

  it('opens with its side and role, and never an index', () => {
    // H-25 puts both squash players on the same half, so seat 3 is not where seat 3 was.
    for (const place of SEAT_PLACES) {
      for (const label of [
        seatLabel(place, { kind: 'you' }),
        seatLabel(place, { kind: 'player', name: 'Marek', level: 2.92 }),
        seatLabel(place, { kind: 'empty' }),
      ]) {
        expect(label.startsWith(PLACE_CLAUSE[place])).toBe(true);
        expect(label).not.toMatch(/\bseat\s*\d/i);
      }
    }
  });

  it('gives every place a phrase, so a place added here cannot ship without words', () => {
    for (const place of SEAT_PLACES) expect(PLACE_CLAUSE[place]).not.toBe('');
  });
});
