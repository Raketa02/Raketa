import type { Wire } from '@/test-support/transport';

import { fillIn, seatToFill } from '@/test-support/groupDeck';

import { toFillIn } from './fillInMappers';

describe('a group’s Fill in', () => {
  it('reads the badge, the clock and each row — its court, share, open seats, deadline and paid players', () => {
    const row = seatToFill();
    const read = toFillIn(fillIn([row]));

    expect(read.badge).toBe(1);
    expect(read.seatsToFill).toHaveLength(1);
    expect(read.seatsToFill[0]).toMatchObject({
      bookingId: row.booking_id,
      sport: 'padel',
      kind: 'competitive',
      startsAt: '2026-10-03T14:00:00Z',
      club: { id: row.club.id, name: 'Ogrody 33' },
      courtName: 'Court 6',
      shareGrosze: 2700,
      openSeats: 1,
      deadline: '2026-10-02T14:00:00Z',
      fillsByTheCutOff: true,
    });
    expect(read.seatsToFill[0]?.players.map((one) => [one.name, one.paid])).toEqual([
      ['Karol Tomaszewski', true],
      ['Ania Kowalska', true],
      ['Kuba Wiśniewski', true],
    ]);
  });

  it('drops a row in a sport this build cannot name, and keeps the rest', () => {
    const kept = seatToFill();
    const read = toFillIn(fillIn([seatToFill({ sport: 'CURLING' as Wire['Sport'] }), kept]));
    expect(read.seatsToFill.map((row) => row.bookingId)).toEqual([kept.booking_id]);
  });
});
