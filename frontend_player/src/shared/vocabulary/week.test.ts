/**
 * The week's own shape: seven days in one order, three parts of a day in one order.
 *
 * Both orders are the **contract's** as well as the design system's, which is why they are
 * asserted at all — `AvailabilitySlotResource` numbers days 1-7 as ISO weekdays and says the
 * grid is Monday-first, so nothing on either side of the wire sorts.
 */

import { DAY_PARTS, WEEKDAYS } from './week';

describe('the shape of the week', () => {
  it('runs Monday to Sunday as ISO weekdays', () => {
    expect(WEEKDAYS).toEqual([1, 2, 3, 4, 5, 6, 7]);
  });

  it('runs the three parts of the day in the order a day runs', () => {
    expect(DAY_PARTS).toEqual(['morning', 'afternoon', 'evening']);
  });
});
