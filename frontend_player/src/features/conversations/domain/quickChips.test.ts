/**
 * The chip row's rule: one question per open slot, and the fallback only on the day itself.
 */

import { quickChips } from './quickChips';

/** 09:00 UTC on the 12th is the 12th in Warsaw, whatever the phone thinks. */
const READ_AT = '2026-09-12T09:00:00Z';

it('asks all three where nothing has been agreed', () => {
  expect(quickChips(undefined, READ_AT)).toEqual(['where', 'day', 'hour']);
});

it('keeps slot order and drops the slots that are filled', () => {
  expect(quickChips({ day: '2026-09-19' }, READ_AT)).toEqual(['where', 'hour']);
  expect(quickChips({ place: 'Zabłocie Sport', day: '2026-09-19' }, READ_AT)).toEqual(['hour']);
});

describe('the fallback', () => {
  it('is offered on the agreed day and on no other', () => {
    expect(quickChips({ day: '2026-09-12' }, READ_AT)).toEqual(['where', 'hour', 'on-my-way']);
    expect(quickChips({ day: '2026-09-13' }, READ_AT)).toEqual(['where', 'hour']);
  });

  it('is never offered where no day is agreed', () => {
    expect(quickChips({ place: 'Zabłocie Sport', hour: '18:00' }, READ_AT)).toEqual(['day']);
  });

  /**
   * *Today* is the platform's day, so a phone somewhere else offers it on the same day
   * everybody else in the room does.
   */
  it('reads today in the platform zone, never the device one', () => {
    const zones = ['Pacific/Kiritimati', 'Pacific/Midway', 'UTC'];
    const read = zones.map((zone) => {
      process.env.TZ = zone;
      return quickChips({ day: '2026-09-12' }, '2026-09-12T21:00:00Z');
    });
    process.env.TZ = 'UTC';

    for (const chips of read) expect(chips).toContain('on-my-way');
  });
});

/**
 * Three unfilled slots plus an unconditional fallback is exactly four, which is what #329 got
 * wrong. Conditional, the two counts cannot both be three.
 */
it('never offers four, whatever is agreed', () => {
  const plans = [
    undefined,
    {},
    { place: 'x' },
    { day: '2026-09-12' },
    { hour: '18:00' },
    { place: 'x', day: '2026-09-12' },
    { place: 'x', hour: '18:00' },
    { day: '2026-09-12', hour: '18:00' },
    { place: 'x', day: '2026-09-12', hour: '18:00' },
  ];

  for (const plan of plans) expect(quickChips(plan, READ_AT).length).toBeLessThanOrEqual(3);
});
