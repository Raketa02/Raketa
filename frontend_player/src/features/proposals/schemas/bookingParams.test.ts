import { parseBookingParams, parseSeatInviteParams } from './bookingParams';

describe('parseBookingParams', () => {
  it('reads a booking id', () => {
    expect(parseBookingParams({ bookingId: '3f2b8c1e-0000-4000-8000-000000000001' })).toEqual({
      bookingId: '3f2b8c1e-0000-4000-8000-000000000001',
    });
  });

  it('refuses anything that is not one', () => {
    expect(parseBookingParams({ bookingId: 'nope' })).toBeUndefined();
    expect(parseBookingParams({})).toBeUndefined();
    expect(
      parseBookingParams({ bookingId: ['3f2b8c1e-0000-4000-8000-000000000001'] }),
    ).toBeUndefined();
  });
});

describe('parseSeatInviteParams', () => {
  const BOOKING = '3f2b8c1e-0000-4000-8000-000000000001';
  const SEAT = 'f0000000-0000-4000-8000-000000000002';

  it('reads the booking and the empty seat it invites into', () => {
    expect(parseSeatInviteParams({ bookingId: BOOKING, seatOf: SEAT })).toEqual({
      bookingId: BOOKING,
      seatOf: SEAT,
    });
  });

  it('refuses a seat it cannot name, or none', () => {
    expect(parseSeatInviteParams({ bookingId: BOOKING })).toBeUndefined();
    expect(parseSeatInviteParams({ bookingId: BOOKING, seatOf: 'nope' })).toBeUndefined();
    expect(parseSeatInviteParams({ bookingId: 'nope', seatOf: SEAT })).toBeUndefined();
  });
});
