/**
 * The slot vocabulary, the two grids and the one cap — everything the card is drawn from that
 * somebody could be **wrong** about.
 *
 * The two grids are the interesting half. Neither is a rule this client invented: the day row is
 * clamped by the game's own horizon and the hour row is a convention the server validates, so what
 * is asserted here is that both agree with the numbers on the other side of the wire, and that the
 * day row **shrinks** rather than offering a day that would be refused.
 */

import {
  HOURS_OFFERED,
  PLACE_CAP,
  PLAN_SLOTS,
  isFilled,
  lastPlannableDay,
  mayRecordPlace,
  offeredDays,
  slotValue,
  tidyPlace,
  unfilledSlots,
  type Plan,
} from './slots';

const CHALLENGE = '11111111-0000-4000-8000-000000000001';

/** Saturday the 12th of September 2026, 09:00 in Warsaw — the day the court filled. */
const PLANNED_AT = '2026-09-12T07:00:00Z';

/** Wednesday the 9th, 09:00 in Warsaw — when the challenge was sent, three days before. */
const SENT_AT = '2026-09-09T07:00:00Z';

function plan(over: Partial<Plan> = {}): Plan {
  return { challengeId: CHALLENGE, anchor: PLANNED_AT, ...over };
}

describe('the slots', () => {
  /** ADR-0144's order, spelled once — the order people discuss them in. */
  it('are where, then the day, then the hour', () => {
    expect(PLAN_SLOTS).toEqual(['where', 'day', 'hour']);
  });

  it('reads each slot’s value off the plan', () => {
    const agreed = plan({ place: 'Zabłocie Sport', day: '2026-09-13', hour: '18:00' });

    expect(slotValue(agreed, 'where')).toBe('Zabłocie Sport');
    expect(slotValue(agreed, 'day')).toBe('2026-09-13');
    expect(slotValue(agreed, 'hour')).toBe('18:00');
  });

  /**
   * *No plan* and *nothing agreed* are one state: `GET /plans` has no row at all for a game
   * nobody has arranged anything on, so a plan that is missing answers exactly as an empty one.
   */
  it('reads a missing plan as three unfilled slots', () => {
    expect(unfilledSlots(undefined)).toEqual(['where', 'day', 'hour']);
    expect(unfilledSlots(plan())).toEqual(['where', 'day', 'hour']);
    expect(isFilled(undefined, 'day')).toBe(false);
  });

  it('reports what is left in slot order', () => {
    expect(unfilledSlots(plan({ day: '2026-09-13' }))).toEqual(['where', 'hour']);
    expect(unfilledSlots(plan({ place: 'x', day: '2026-09-13', hour: '18:00' }))).toEqual([]);
  });
});

describe('the day row', () => {
  /** Seven chips, today + 6 — and *today* is the platform's, never the device's. */
  it('offers today and the six days after it', () => {
    expect(offeredDays({ readAt: PLANNED_AT, anchor: PLANNED_AT })).toEqual([
      '2026-09-12',
      '2026-09-13',
      '2026-09-14',
      '2026-09-15',
      '2026-09-16',
      '2026-09-17',
      '2026-09-18',
    ]);
  });

  /** `anchor + PLAN_HORIZON`, read as a local day — the clamp, mirrored from the server. */
  it('stops at the row’s own horizon', () => {
    expect(lastPlannableDay(PLANNED_AT)).toBe('2026-09-19');
  });

  /**
   * **Before the game exists the anchor is the send** (ADR-0164 §4), so a room whose court is still
   * filling offers a shorter row — and the same seven days once it fills, because the anchor only
   * ever moves later and nothing already chosen becomes invalid.
   */
  it('runs from the send while the court is filling, and widens when it fills', () => {
    expect(offeredDays({ readAt: PLANNED_AT, anchor: SENT_AT })).toEqual([
      '2026-09-12',
      '2026-09-13',
      '2026-09-14',
      '2026-09-15',
      '2026-09-16',
    ]);
    expect(offeredDays({ readAt: PLANNED_AT, anchor: PLANNED_AT })).toHaveLength(7);
  });

  /**
   * The row **shrinks as the week runs out**, which is the whole reason it is clamped rather
   * than merely seven long: a day past the horizon is one `PUT /plans/{id}/day` refuses.
   */
  it('shrinks a day at a time as the horizon runs out', () => {
    const days = (readAt: string) => offeredDays({ readAt, anchor: PLANNED_AT });

    expect(days('2026-09-13T07:00:00Z')).toHaveLength(7);
    expect(days('2026-09-14T07:00:00Z')).toHaveLength(6);
    expect(days('2026-09-18T07:00:00Z')).toHaveLength(2);
    expect(days('2026-09-19T07:00:00Z')).toEqual(['2026-09-19']);
  });

  /**
   * **Inside the entry grace no day may be set.** Entry closes a grace after the horizon, so
   * there is a day at the end of every game's life where the plan can no longer name one — and a
   * row of no chips is the honest drawing of it.
   */
  it('offers nothing at all once the horizon has passed', () => {
    expect(offeredDays({ readAt: '2026-09-20T07:00:00Z', anchor: PLANNED_AT })).toEqual([]);
  });

  it('offers nothing where either instant is unreadable', () => {
    expect(offeredDays({ readAt: 'Saturday', anchor: PLANNED_AT })).toEqual([]);
    expect(offeredDays({ readAt: PLANNED_AT, anchor: '' })).toEqual([]);
  });
});

describe('the hour row', () => {
  /** 30-minute steps between 06:00 and 23:00, which is the grid the server validates against. */
  it('runs from 06:00 to 23:00 in half hours', () => {
    expect(HOURS_OFFERED[0]).toBe('06:00');
    expect(HOURS_OFFERED[1]).toBe('06:30');
    expect(HOURS_OFFERED.at(-1)).toBe('23:00');
    expect(HOURS_OFFERED).toHaveLength(35);
  });

  it('draws every hour zero-padded, so a column of them does not ripple', () => {
    expect(HOURS_OFFERED.every((hour) => /^\d\d:(00|30)$/.test(hour))).toBe(true);
  });
});

describe('what may be written in the where box', () => {
  /** Runs of whitespace collapse to one space, so the value is one line. The server's own rule. */
  it('collapses a value to one line', () => {
    expect(tidyPlace('  Zabłocie   Sport\n court 3 ')).toBe('Zabłocie Sport court 3');
  });

  /** **A slot is never emptied**, so a blank box is not a way of clearing one. */
  it('refuses a box holding nothing but whitespace', () => {
    expect(mayRecordPlace('')).toBe(false);
    expect(mayRecordPlace('   \n ')).toBe(false);
    expect(mayRecordPlace('Zabłocie Sport')).toBe(true);
  });

  /** Measured on the tidied value, because that is what would be stored and shown. */
  it('refuses a value past the cap and accepts one at it', () => {
    expect(mayRecordPlace('x'.repeat(PLACE_CAP))).toBe(true);
    expect(mayRecordPlace('x'.repeat(PLACE_CAP + 1))).toBe(false);
    expect(mayRecordPlace(`${' '.repeat(20)}${'x'.repeat(PLACE_CAP)}${' '.repeat(20)}`)).toBe(true);
  });
});
