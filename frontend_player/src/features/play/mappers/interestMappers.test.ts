/**
 * The **Match me count**, and the one thing about it worth pinning: it is the *outstanding*
 * figure the contract publishes rather than a length this app derives.
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
  it('answers for every sport in one map', () => {
    expect(
      toOutstandingInterest(
        list({
          outstanding: [
            { sport: 'PADEL', outstanding: 3, cap: 10 },
            { sport: 'TENNIS', outstanding: 0, cap: 10 },
          ],
        }),
      ),
    ).toEqual({ padel: 3, tennis: 0 });
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
            { sport: 'PADEL', outstanding: 3, cap: 10 },
            { sport: 'PICKLEBALL' as never, outstanding: 9, cap: 10 },
          ],
        }),
      ),
    ).toEqual({ padel: 3 });
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
    expect(toOutstandingAfterTap({ sport: 'PADEL', outstanding: 4, cap: 10 })).toEqual({
      padel: 4,
    });
  });
});
