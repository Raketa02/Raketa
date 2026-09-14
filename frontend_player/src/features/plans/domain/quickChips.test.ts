/**
 * The chip row's rule: one question per open slot, and the fallback only on the day itself.
 *
 * The slot order it keeps is `slots.ts`' and is asserted there; what is asserted here is only the
 * two things this rule adds — which slots are dropped, and when the fallback is offered.
 */

import { setDeviceZone } from '@/test-support/deviceZone';

import { quickChips } from './quickChips';
import type { Plan } from './slots';

const CHALLENGE = '11111111-0000-4000-8000-000000000001';

/** A plan holding whatever the case is about. The key and the anchor are identity; no rule here reads them. */
function plan(over: Partial<Plan> = {}): Plan {
  return { challengeId: CHALLENGE, anchor: '2026-09-08T09:00:00Z', ...over };
}

const DEVICE_ZONE = process.env.TZ;

// Restored here rather than at the end of the test that moves it: a failing expectation would
// otherwise leak a zone into every suite after this one, and those are the suites about days.
afterEach(() => {
  setDeviceZone(DEVICE_ZONE);
});

/** 09:00 UTC on the 12th is the 12th in Warsaw, whatever the phone thinks. */
const READ_AT = '2026-09-12T09:00:00Z';

it('asks all three where nothing has been agreed', () => {
  expect(quickChips(undefined, READ_AT)).toEqual(['where', 'day', 'hour']);
});

it('keeps slot order and drops the slots that are filled', () => {
  expect(quickChips(plan({ day: '2026-09-19' }), READ_AT)).toEqual(['where', 'hour']);
  expect(quickChips(plan({ place: 'Zabłocie Sport', day: '2026-09-19' }), READ_AT)).toEqual([
    'hour',
  ]);
});

describe('the fallback', () => {
  it('is offered on the agreed day and on no other', () => {
    expect(quickChips(plan({ day: '2026-09-12' }), READ_AT)).toEqual([
      'where',
      'hour',
      'on-my-way',
    ]);
    expect(quickChips(plan({ day: '2026-09-13' }), READ_AT)).toEqual(['where', 'hour']);
  });

  it('is never offered where no day is agreed', () => {
    expect(quickChips(plan({ place: 'Zabłocie Sport', hour: '18:00' }), READ_AT)).toEqual(['day']);
  });

  /**
   * *Today* is the platform's day, so a phone somewhere else offers it on the same day
   * everybody else in the room does.
   */
  it('reads today in the platform zone, never the device one', () => {
    const zones = ['Pacific/Kiritimati', 'Pacific/Midway', 'UTC'];
    const read = zones.map((zone) => {
      setDeviceZone(zone);
      return quickChips(plan({ day: '2026-09-12' }), '2026-09-12T21:00:00Z');
    });

    for (const chips of read) expect(chips).toContain('on-my-way');
  });
});

/**
 * Three unfilled slots plus an unconditional fallback is exactly four, which is what #329 got
 * wrong. Conditional, the two counts cannot both be three.
 */
it('never offers four, whatever is agreed', () => {
  const every: readonly (Plan | undefined)[] = [
    undefined,
    plan(),
    plan({ place: 'x' }),
    plan({ day: '2026-09-12' }),
    plan({ hour: '18:00' }),
    plan({ place: 'x', day: '2026-09-12' }),
    plan({ place: 'x', hour: '18:00' }),
    plan({ day: '2026-09-12', hour: '18:00' }),
    plan({ place: 'x', day: '2026-09-12', hour: '18:00' }),
  ];

  for (const one of every) expect(quickChips(one, READ_AT).length).toBeLessThanOrEqual(3);
});
