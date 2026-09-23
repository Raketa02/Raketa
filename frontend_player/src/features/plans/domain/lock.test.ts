/**
 * The lock — the count it is guarded on, and the control's five states as a pure function of the
 * plan and the court
 * ([ADR-0155](../../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md),
 * [ADR-0164](../../../../../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md)
 * §5).
 *
 * **The count and the lock are two facts**, and that is what is asserted: three filled slots is a
 * plan everybody *could* agree, and only `lockedAt` says somebody did. **And the lock waits for the
 * court**: while the room has no game the control is not drawn at all, whatever the count.
 */

import type { Plan } from './slots';
import { LINE_UP_COMPLETE, SLOTS, isLocked, lockControl, slotCount, type LineUp } from './lock';

const CHALLENGE = '11111111-0000-4000-8000-000000000001';

function plan(over: Partial<Plan> = {}): Plan {
  return { challengeId: CHALLENGE, anchor: '2026-09-12T07:00:00Z', ...over };
}

/** Two of a padel four are in, and the room has no game. */
const TWO_OF_FOUR: LineUp = { complete: false, members: 2, seats: 4 };

/** The court has its game — the fold's ordinary input, spelled once. */
const WHOLE = { pending: false, lineUp: LINE_UP_COMPLETE } as const;

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
    expect(lockControl(undefined, WHOLE)).toBe('greyed');
    expect(lockControl(plan({ day: '2026-09-13' }), WHOLE)).toBe('greyed');
    expect(lockControl(plan({ place: 'x', day: '2026-09-13' }), WHOLE)).toBe('greyed');
  });

  it('is live once all three are set', () => {
    expect(lockControl(COMPLETE, WHOLE)).toBe('live');
  });

  /** Pending, never optimistic: the press is blocked and the word changes, nothing else does. */
  it('is busy while the lock is going out', () => {
    expect(lockControl(COMPLETE, { ...WHOLE, pending: true })).toBe('busy');
  });

  /**
   * Once locked the control is **gone** rather than settled: a second lock records nothing and
   * answers `200`, so a control still offering it would be one that provably does nothing.
   */
  it('is gone once the plan is locked', () => {
    const locked = { ...COMPLETE, lockedAt: '2026-09-12T10:00:00Z' };

    expect(lockControl(locked, WHOLE)).toBe('gone');
    expect(lockControl(locked, { ...WHOLE, pending: true })).toBe('gone');
  });

  /**
   * **The lock waits for the court** (ADR-0164 §5): while the room has no game the control is not
   * drawn — absent, never greyed, on #324's rule — and the count line stands where it will be. The
   * count of slots says nothing here: three of three set by two of four is still a plan nobody may
   * agree for four.
   */
  it('waits for the court while the line-up is incomplete, whatever the count', () => {
    const filling = { pending: false, lineUp: TWO_OF_FOUR } as const;

    expect(lockControl(undefined, filling)).toBe('waiting');
    expect(lockControl(plan({ day: '2026-09-13' }), filling)).toBe('waiting');
    expect(lockControl(COMPLETE, filling)).toBe('waiting');
  });

  /**
   * The line-up having completed is the whole of the rule — *has this court become a game* — so a
   * game a seat has since been left open on is still complete and still offers the lock; what the
   * server says to that is a sentence, not a state.
   */
  it('is offered the moment the line-up has completed, and stays offered', () => {
    expect(lockControl(COMPLETE, WHOLE)).toBe('live');
    expect(lockControl(plan(), WHOLE)).toBe('greyed');
  });
});
