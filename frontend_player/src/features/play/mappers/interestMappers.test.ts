/**
 * Where each sport stands against its cap — and the three things about it worth pinning: it is
 * the *outstanding* figure the contract publishes rather than a length this app derives, the
 * cap and the life of a yes cross **beside** it rather than being held here, and the two lists
 * beside the rows stop at this boundary.
 *
 * *"Outstanding means sent, unexpired and not yet mutual"* — a rule about the server's clock
 * and about a yes that has come back, neither of which a phone can evaluate. Counting the
 * `outgoing` list instead would be this app answering a question the response already answers,
 * differently.
 */

import type { Wire } from '@/test-support/transport';

import { toOutstandingAfterTap, toOutstandingInterest } from './interestMappers';

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
      toOutstandingInterest(
        list({
          outstanding: [
            { sport: 'PADEL', outstanding: 3, cap: 20, ttl_days: 21 },
            { sport: 'TENNIS', outstanding: 0, cap: 10, ttl_days: 14 },
          ],
        }),
      ),
    ).toEqual({
      padel: { outstanding: 3, cap: 20, ttlDays: 21 },
      tennis: { outstanding: 0, cap: 10, ttlDays: 14 },
    });
  });

  /** An absent sport is *nothing outstanding there*, which is what the route means by silence. */
  it('is partial, so a sport with no row simply has no entry', () => {
    expect(toOutstandingInterest(list())).toEqual({});
  });

  it('drops a sport this build cannot name, rather than keying a map by a wire code', () => {
    expect(
      toOutstandingInterest(
        list({
          outstanding: [
            { sport: 'PADEL', outstanding: 3, cap: 10, ttl_days: 21 },
            { sport: 'PICKLEBALL' as never, outstanding: 9, cap: 10, ttl_days: 21 },
          ],
        }),
      ),
    ).toEqual({ padel: { outstanding: 3, cap: 10, ttlDays: 21 } });
  });

  /**
   * The rows themselves stop at this boundary: a `player_id` and an `expires_at` are *You*'s
   * screen, and a mapper carrying them would be a list nothing draws.
   */
  it('reads nothing from the two lists beside it', () => {
    const outgoing = [
      {
        player_id: 'aaaaaaaa-0000-4000-8000-000000000001',
        sport: 'PADEL' as const,
        at: '2026-09-01T18:00:00Z',
        expires_at: '2026-09-08T18:00:00Z',
      },
    ];

    expect(toOutstandingInterest(list({ outgoing, mutual: outgoing }))).toEqual({});
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
