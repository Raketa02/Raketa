/**
 * The live yeses off the wire: the pool read as the group it is filed under, the kind in the
 * switch's spelling, the book-by as the card's deadline — and a sport this build cannot name
 * dropped rather than drawn.
 */

import { liveYes } from '@/test-support/groupDeck';

import { toLiveYes, toLiveYeses } from './liveYesMappers';

describe('a live yes', () => {
  it('reads every field the row and the details draw', () => {
    const wire = liveYes({ kind: 'FOR_FUN' });

    expect(toLiveYes(wire)).toEqual({
      proposalId: wire.proposal_id,
      groupId: wire.pool_id,
      sport: 'padel',
      kind: 'forFun',
      startsAt: '2026-10-03T13:00:00Z',
      club: { id: wire.club.id, name: 'Bonarka Arena' },
      shareGrosze: 2800,
      deadline: wire.book_by,
    });
  });

  it('carries the court’s kind when the game promises one, and leaves it off when mixed', () => {
    expect(toLiveYes(liveYes({ indoor: true }))?.indoor).toBe(true);
    expect(toLiveYes(liveYes({ indoor: false }))?.indoor).toBe(false);
    expect(toLiveYes(liveYes({ indoor: null }))).not.toHaveProperty('indoor');
  });

  it('leaves the name off a club that no longer exists', () => {
    const read = toLiveYes(
      liveYes({ club: { id: 'b0000000-0000-4000-8000-000000000009', name: null } }),
    );
    expect(read?.club).toEqual({ id: 'b0000000-0000-4000-8000-000000000009' });
  });
});

describe('the list', () => {
  it('keeps the server’s order', () => {
    const first = liveYes();
    const second = liveYes({ sport: 'TENNIS' });

    const read = toLiveYeses({ yeses: [first, second] });

    expect(read.yeses.map((yes) => [yes.proposalId, yes.sport])).toEqual([
      [first.proposal_id, 'padel'],
      [second.proposal_id, 'tennis'],
    ]);
  });

  it('drops a yes in a sport this build cannot name', () => {
    const unknown = { ...liveYes(), sport: 'PICKLEBALL' } as unknown as ReturnType<typeof liveYes>;

    expect(toLiveYeses({ yeses: [unknown, liveYes()] }).yeses).toHaveLength(1);
  });
});
