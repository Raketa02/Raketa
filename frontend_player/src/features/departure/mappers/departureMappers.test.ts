/**
 * The wire's departure, mapped.
 *
 * What is asserted here is the part no rendered test can see: which fields cross,
 * which are dropped, and what an answer this build cannot read fully turns into.
 */

import {
  committedOutcomes,
  departureScreen,
  departureWrite,
  outcomeRow,
} from '@/test-support/departure';
import { matchCard } from '@/test-support/now';
import type { Wire } from '@/test-support/transport';

import { toDeparture, toDepartureAnswer } from './departureMappers';

const MATCH = '5b0c0000-0000-4000-8000-000000000001';

describe('the screen', () => {
  it('carries the spine, the quote and all four outcomes', () => {
    const screen = toDeparture(departureScreen({ matchId: MATCH, amount: 3800 }));

    expect(screen.matchId).toBe(MATCH);
    expect(screen.where.clubName).toBe('Sunset Padel');
    expect(screen.price).toEqual({ amount: 3800, currency: 'PLN' });
    expect(screen.quote.outcome).toBe('refundedInFull');
    expect(screen.outcomes).toHaveLength(4);
  });

  it('resolves the match’s own situation through Now’s table', () => {
    // The wire embeds the spine and the situation half verbatim, so this screen
    // and the card she tapped say the same sentence about the same match. A table
    // copied into this feature is how the two come to disagree.
    const screen = toDeparture(departureScreen({ matchId: MATCH, situation: 'forming' }));

    expect(screen.status?.line).toBe('Not held — Sunset Padel is still selling this slot.');
  });

  it('draws a moment on the row that opens and on no other', () => {
    const screen = toDeparture(
      departureScreen({
        matchId: MATCH,
        outcomes: committedOutcomes('2026-08-23T18:00:00Z', '2026-08-23T20:00:00Z'),
      }),
    );

    expect(screen.outcomes.map((row) => row.opensAt)).toEqual([
      undefined,
      undefined,
      '2026-08-23T18:00:00Z',
      '2026-08-23T20:00:00Z',
    ]);
  });

  it('takes the row count from the server and never pads it to four', () => {
    // A private court sends **two** rows, because only two outcomes are reachable
    // there. A client that filled the table out to four would be inventing two
    // outcomes this match cannot produce.
    const screen = toDeparture(
      departureScreen({
        matchId: MATCH,
        outcomes: [
          outcomeRow('refundedInFull', 'searching'),
          outcomeRow('forfeited', 'opens', '2026-08-24T19:00:00Z'),
        ],
        commitmentDeadline: null,
      }),
    );

    expect(screen.outcomes).toHaveLength(2);
    // No commitment on a private court: the court was bought at booking, so there
    // is no commitment for a deadline to be about. Absent, never zero.
    expect(screen.commitmentDeadline).toBeUndefined();
  });

  it('counts by money and drops the number a played match would carry', () => {
    const screen = toDeparture(
      departureScreen({ matchId: MATCH, counts: { seats: 4, paid: 3, held: 1, turned_up: 3 } }),
    );

    expect(screen.counts).toEqual({ seats: 4, paid: 3, held: 1 });
  });

  it('leaves an outcome this build has never heard of without words', () => {
    // The row is dropped by the table rather than drawn blank, and the quote's
    // absent copy is what withholds the button — a control whose consequence the
    // app cannot state is the one outcome worse than silence.
    const wire = departureScreen({ matchId: MATCH });
    const unknown = { ...wire, quote: 'transferred' as Wire['Outcome'] };

    const screen = toDeparture(unknown);

    expect(screen.quote.outcome).toBe('transferred');
    expect(screen.quote.copy).toBeUndefined();
  });
});

describe('a write’s answer', () => {
  const screen = departureScreen({ matchId: MATCH, mayDepart: false });
  const card = matchCard({ matchId: MATCH, situation: 'rescue' });

  it('says what the tap applied', () => {
    const answer = toDepartureAnswer(departureWrite(screen, card, 'refundedInFull'));

    expect(answer.applied?.outcome).toBe('refundedInFull');
    expect(answer.applied?.copy?.left).toBe('You have left. You are refunded in full.');
  });

  it('says nothing was applied when nothing was', () => {
    // `applied` absent is the **only** thing its absence can mean, and it is what
    // stops *was I refused* being derived from `mayDepart` still being true.
    const answer = toDepartureAnswer(departureWrite(screen, card, null));

    expect(answer.applied).toBeUndefined();
    expect(answer.screen.mayDepart).toBe(false);
  });

  it('carries Now’s one changed card, mapped as a compose would map it', () => {
    const answer = toDepartureAnswer(departureWrite(screen, card, 'refundedInFull'));

    expect(answer.update.card.matchId).toBe(MATCH);
    expect(answer.update.card.status?.tag).toBe('Rescue active');
  });
});
