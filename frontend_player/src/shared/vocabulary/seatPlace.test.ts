/**
 * Where a seat is — **a side and a role, read off the line-up and never off the drawing** (H-25).
 *
 * The rule came here from Play's builder (#574), and the group page's Friends court is the reader
 * that stays: one seat that is yours and every other seat open, a line-up nobody is in yet.
 */

import { theme } from '@/shared/ui/theme';

import { SEAT_PLACES, seatPlaces, type LineUpSeat } from './seatPlace';

const YOU: LineUpSeat = { kind: 'you' };
const SOMEBODY: LineUpSeat = { kind: 'player' };
const NOBODY: LineUpSeat = { kind: 'empty' };

describe("a seat's place", () => {
  it('is a side and a role, read off seat order rather than off the drawing', () => {
    expect(seatPlaces([YOU, SOMEBODY, SOMEBODY, SOMEBODY])).toEqual([
      'YOUR_SIDE',
      'YOUR_PARTNER',
      'THEIR_SIDE',
      'THEIR_SIDE',
    ]);
  });

  it('has no partner in singles, because your half has one seat in it', () => {
    expect(seatPlaces([YOU, SOMEBODY])).toEqual(['YOUR_SIDE', 'THEIR_SIDE']);
  });

  it('follows you across the net, because a side is the half you are on', () => {
    expect(seatPlaces([SOMEBODY, SOMEBODY, YOU, SOMEBODY])).toEqual([
      'THEIR_SIDE',
      'THEIR_SIDE',
      'YOUR_SIDE',
      'YOUR_PARTNER',
    ]);
  });

  it('cannot be derived from where a seat is drawn, and squash is why (H-25)', () => {
    // Both squash seats are on the near half of the drawing; a rule that read the far side off
    // the coordinate would put both players on your side.
    const [near, far] = theme.size.court.seats.squash;
    const half = theme.size.court.space.height / 2;

    expect(near?.[1]).toBeGreaterThan(half);
    expect(far?.[1]).toBeGreaterThanOrEqual(half);
    expect(seatPlaces([YOU, SOMEBODY])).toEqual(['YOUR_SIDE', 'THEIR_SIDE']);
  });

  it('places an open seat by where it is, as the Friends court reads its line-up', () => {
    expect(seatPlaces([YOU, NOBODY, NOBODY, NOBODY])).toEqual([
      'YOUR_SIDE',
      'YOUR_PARTNER',
      'THEIR_SIDE',
      'THEIR_SIDE',
    ]);
  });

  it('reads a court that seats nobody as the court it started as — you in the first seat', () => {
    expect(seatPlaces([NOBODY, NOBODY, NOBODY, NOBODY])).toEqual([
      'YOUR_SIDE',
      'YOUR_PARTNER',
      'THEIR_SIDE',
      'THEIR_SIDE',
    ]);
  });

  it('names three places and no fourth — nobody is seated relative to their partner', () => {
    expect(SEAT_PLACES).toEqual(['YOUR_SIDE', 'YOUR_PARTNER', 'THEIR_SIDE']);
  });
});
