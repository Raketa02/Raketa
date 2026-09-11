/**
 * The lock — the count it is guarded on, and the control's four states as a pure function of the
 * plan ([ADR-0155](../../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)).
 *
 * **The count and the lock are two facts**, and that is what is asserted: three filled slots is a
 * plan everybody *could* agree, and only `lockedAt` says somebody did.
 */

import type { Plan } from './slots';
import { SLOTS, isLocked, lockControl, slotCount } from './lock';

const GAME = '11111111-0000-4000-8000-000000000001';

function plan(over: Partial<Plan> = {}): Plan {
  return { gameId: GAME, ...over };
}

const COMPLETE = plan({ place: 'Zabłocie Sport', day: '2026-09-13', hour: '18:00' });

describe('the count', () => {
  it('is three slots, and never a fourth', () => {
    expect(SLOTS).toBe(3);
  });

  /** *No plan* and *nothing agreed* are one state, so a missing plan counts as nought. */
  it('counts the filled slots, from none to all three', () => {
    expect(slotCount(undefined)).toBe(0);
    expect(slotCount(plan())).toBe(0);
    expect(slotCount(plan({ day: '2026-09-13' }))).toBe(1);
    expect(slotCount(plan({ place: 'Zabłocie Sport', hour: '18:00' }))).toBe(2);
    expect(slotCount(COMPLETE)).toBe(3);
  });
});

describe('the lock', () => {
  /** ADR-0155 §3: `is_locked` is **explicitly not** `slot_count == SLOTS`. */
  it('is not the count under another name', () => {
    expect(isLocked(COMPLETE)).toBe(false);
    expect(isLocked({ ...COMPLETE, lockedAt: '2026-09-12T10:00:00Z' })).toBe(true);
    expect(isLocked(undefined)).toBe(false);
  });
});

describe('the control', () => {
  it('is greyed while any slot is empty', () => {
    expect(lockControl(undefined, { pending: false })).toBe('greyed');
    expect(lockControl(plan({ day: '2026-09-13' }), { pending: false })).toBe('greyed');
    expect(lockControl(plan({ place: 'x', day: '2026-09-13' }), { pending: false })).toBe('greyed');
  });

  it('is live once all three are set', () => {
    expect(lockControl(COMPLETE, { pending: false })).toBe('live');
  });

  /** Pending, never optimistic: the press is blocked and the word changes, nothing else does. */
  it('is busy while the lock is going out', () => {
    expect(lockControl(COMPLETE, { pending: true })).toBe('busy');
  });

  /**
   * Once locked the control is **gone** rather than settled: a second lock records nothing and
   * answers `200`, so a control still offering it would be one that provably does nothing.
   */
  it('is gone once the plan is locked', () => {
    const locked = { ...COMPLETE, lockedAt: '2026-09-12T10:00:00Z' };

    expect(lockControl(locked, { pending: false })).toBe('gone');
    expect(lockControl(locked, { pending: true })).toBe('gone');
  });
});
