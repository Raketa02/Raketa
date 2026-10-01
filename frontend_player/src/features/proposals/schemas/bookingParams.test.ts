import { parseBookingParams } from './bookingParams';

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
