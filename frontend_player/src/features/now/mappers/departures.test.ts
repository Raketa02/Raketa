/**
 * A leaver's own money, in the one line her card gains.
 *
 * The pair of assertions that matter is *what she paid is named* against *no
 * amount is named at all*, because that pair is the whole reason the wire carries
 * two payload forms rather than one with an optional figure: **nothing was taken**
 * and **nothing has come back yet** are opposite sentences and a blank cannot tell
 * them apart.
 */

import { leftHavingPaid, leftHavingPaidNothing } from '@/test-support/departure';
import type { Wire } from '@/test-support/transport';

import { LEAVER_COPY, LEAVER_NOTHING_TAKEN, leaverLine } from './departures';

/**
 * `38,00 zł` with the **non-breaking** space the shared table renders, so a price
 * never wraps mid-number. Written out rather than composed with `formatMoney`,
 * because a literal is what makes this an assertion about the sentence rather than
 * a comparison of the code against itself.
 */
const PAID = '38,00\u00a0zł';

describe('the table itself', () => {
  it('holds exactly the four outcomes, so a fifth is a decision', () => {
    // The `Record` forces a fifth row to be *written*; it cannot force anybody to
    // notice that a fifth outcome now exists. This is where growth stops and
    // somebody chooses — the same guard the other tables in this feature carry.
    expect(Object.keys(LEAVER_COPY).sort()).toEqual([
      'forfeited',
      'refundedHalf',
      'refundedInFull',
      'reversed',
    ]);
  });

  it('says something in every row, and names the money in every one', () => {
    // A row satisfying the `Record` with `''` typechecks perfectly and ships the
    // exact defect the table exists to prevent.
    for (const entry of Object.values(LEAVER_COPY)) {
      expect(entry(PAID)).toContain(PAID);
      expect(entry(PAID).length).toBeGreaterThan(PAID.length);
    }
  });
});

describe('a leaver who paid', () => {
  it('is told what she paid while nothing has decided it', () => {
    // The condition and never a moment: what stands between her and her money is
    // somebody taking the seat, and nothing can say when that will be.
    expect(leaverLine(leftHavingPaid(3800))).toBe(
      `You left — ${PAID} comes back if somebody takes your seat.`,
    );
  });

  it('is told what became of it once something has', () => {
    expect(leaverLine(leftHavingPaid(3800, 'refundedInFull'))).toBe(
      `You left — ${PAID} is coming back in full.`,
    );
    expect(leaverLine(leftHavingPaid(3800, 'refundedHalf'))).toBe(
      `You left — half of ${PAID} is coming back.`,
    );
    expect(leaverLine(leftHavingPaid(3800, 'reversed'))).toBe(
      `You left — ${PAID} was reversed, as though it never left.`,
    );
  });

  it('keeps the figure on a forfeit, where it is what it cost her', () => {
    // `Recoverable` names what she paid **in**; whether any of it comes back is
    // the outcome's answer, so a forfeited departure still carries the figure.
    // Dropping it here would be the one sentence a blank swallows entirely.
    expect(leaverLine(leftHavingPaid(3800, 'forfeited'))).toBe(
      `You left — ${PAID} stayed with the match.`,
    );
  });

  it('never works out half of it for itself', () => {
    // Halving is arithmetic, and the phone does none (`ADR-0053`). The server
    // sends what she paid rather than what she recovered, so the sentence names
    // the amount she knows.
    expect(leaverLine(leftHavingPaid(3800, 'refundedHalf'))).not.toContain('19,00');
  });
});

describe('a leaver who paid nothing', () => {
  it('sees a line naming no amount at all', () => {
    // `Raketa02/Raketa#91`: *she is not invited to interpret a blank*.
    const line = leaverLine(leftHavingPaidNothing());

    expect(line).toBe(LEAVER_NOTHING_TAKEN);
    expect(line).not.toMatch(/\d/);
    expect(line).not.toContain('zł');
  });
});

describe('everybody else', () => {
  it('has no line, because the payload is not there', () => {
    expect(leaverLine(null)).toBeUndefined();
    expect(leaverLine(undefined)).toBeUndefined();
  });

  it('loses the sentence and nothing else on an outcome this build cannot name', () => {
    // The card still says what the match is doing, which is the fact her money
    // turns on. A blank line under the situation would be a new defect.
    // Through `unknown`, because the union deliberately admits only the four —
    // which is the whole point of the guard being tested. A build that could
    // express this in the type system would not need the runtime fallback.
    const fifth = {
      form: 'recoverable',
      paid: { amount: 3800, currency: 'PLN' },
      outcome: 'transferred',
    } as unknown as Wire['SituationFactsResponse']['departure'];

    expect(leaverLine(fifth)).toBeUndefined();
  });
});
