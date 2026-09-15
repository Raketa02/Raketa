/**
 * Your own yeses, as one read — where each sport stands against its cap, and **who** you said
 * it to — and the things about it worth pinning: the count is the *outstanding* figure the
 * contract publishes rather than a length this app derives, the cap and the life of a yes cross
 * **beside** it rather than being held here, the outgoing list crosses as **ids per sport and
 * nothing else**, and the mutual list stops at this boundary.
 *
 * *"Outstanding means sent, unexpired and not yet mutual"* — a rule about the server's clock
 * and about a yes that has come back, neither of which a phone can evaluate. Counting the
 * `outgoing` list instead would be this app answering a question the response already answers,
 * differently.
 */

import { outgoingYes as sent } from '@/test-support/onboardingRouter';
import type { Wire } from '@/test-support/transport';

import { toInterest, toOutstandingAfterTap } from './interestMappers';

const ANIA = 'aaaaaaaa-0000-4000-8000-000000000001';
const MAREK = 'bbbbbbbb-0000-4000-8000-000000000002';

function list(over: Partial<Wire['InterestListResponse']> = {}): Wire['InterestListResponse'] {
  return { outgoing: [], mutual: [], outstanding: [], ...over };
}

describe('the read', () => {
  /**
   * Three numbers per sport, all the server's: the count the counter subtracts from the cap,
   * the cap itself — ruleset configuration, *read it from here, never hardcode it* — and how
   * long a yes lives, which the ending prints without the client holding the number
   * (ADR-0127 §6 as amended by ADR-0169 §5).
   */
  it('answers for every sport in one map, with the cap and the life of a yes beside the count', () => {
    expect(
      toInterest(
        list({
          outstanding: [
            { sport: 'PADEL', outstanding: 3, cap: 20, ttl_days: 21 },
            { sport: 'TENNIS', outstanding: 0, cap: 10, ttl_days: 14 },
          ],
        }),
      ).standing,
    ).toEqual({
      padel: { outstanding: 3, cap: 20, ttlDays: 21 },
      tennis: { outstanding: 0, cap: 10, ttlDays: 14 },
    });
  });

  /** An absent sport is *nothing outstanding there*, which is what the route means by silence. */
  it('is partial, so a sport with no row simply has no entry', () => {
    expect(toInterest(list())).toEqual({ standing: {}, outgoing: {} });
  });

  it('drops a sport this build cannot name, rather than keying a map by a wire code', () => {
    expect(
      toInterest(
        list({
          outstanding: [
            { sport: 'PADEL', outstanding: 3, cap: 10, ttl_days: 21 },
            { sport: 'PICKLEBALL' as never, outstanding: 9, cap: 10, ttl_days: 21 },
          ],
          outgoing: [sent(ANIA, 'PADEL'), sent(MAREK, 'PICKLEBALL' as never)],
        }),
      ),
    ).toEqual({
      standing: { padel: { outstanding: 3, cap: 10, ttlDays: 21 } },
      outgoing: { padel: [ANIA] },
    });
  });

  /**
   * **Who** you said yes to, per sport, in the order the wire sent them — the fact *You said
   * yes* is drawn from on the builder's cards and the challenge screen (ADR-0169 §8). Ids and
   * nothing else: `at` and `expires_at` stop here, because nothing draws a list of your yeses
   * and nothing may hold a date this side that the server's clock owns.
   */
  it('carries the outgoing ids per sport, and nothing else about them', () => {
    expect(
      toInterest(
        list({ outgoing: [sent(ANIA, 'PADEL'), sent(MAREK, 'PADEL'), sent(MAREK, 'TENNIS')] }),
      ).outgoing,
    ).toEqual({ padel: [ANIA, MAREK], tennis: [MAREK] });
  });

  /**
   * A mutual has come back and is not *outgoing*: it is the list *You said yes* must never read,
   * because the person it names has already matched the reader.
   */
  it('reads nothing from the mutual list', () => {
    expect(toInterest(list({ mutual: [sent(ANIA, 'PADEL')] })).outgoing).toEqual({});
  });
});

describe('the tap’s own answer', () => {
  /**
   * The response carries where the sport stands **after** the tap, so the number moves without
   * a second round trip — Part 7's *"don't immediately refetch what you were just handed"*.
   */
  it('is the same shape, for the one sport the tap was about', () => {
    expect(
      toOutstandingAfterTap({ sport: 'PADEL', outstanding: 4, cap: 10, ttl_days: 21 }),
    ).toEqual({
      padel: { outstanding: 4, cap: 10, ttlDays: 21 },
    });
  });
});
