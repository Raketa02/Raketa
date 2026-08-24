/**
 * The wire's result screen, mapped.
 *
 * What is asserted here is the part no rendered test can see: which fields cross,
 * which are dropped, and what an answer this build cannot read fully turns into.
 */

import { matchCard } from '@/test-support/now';
import { emptyResultBlock, resultScreen, resultWrite, scoreLine } from '@/test-support/result';
import type { Wire } from '@/test-support/transport';

import { ENDING_COPY } from './endings';
import { toResult, toResultAnswer } from './resultMappers';

const MATCH = '5b0c0000-0000-4000-8000-000000000001';

/** A live proposal from the other side: the shape three of the six renderings use. */
function proposed(by: number): Wire['ResultBlockResponse'] {
  return {
    agreed: false,
    proposals: 1,
    score: scoreLine(
      [
        ['Ada', 'Kuba'],
        ['Marta', 'Ola'],
      ],
      [
        [6, 4],
        [3, 6],
      ],
    ),
    proposed_by: by,
  };
}

describe('the screen', () => {
  it('carries the spine, the three booleans and both clocks', () => {
    const screen = toResult(
      resultScreen({
        matchId: MATCH,
        amount: 3800,
        mayAccept: true,
        mayCounter: true,
        settlementDeadline: '2026-08-24T18:00:00Z',
        acceptanceGrace: '2026-08-23T18:30:00Z',
      }),
    );

    expect(screen.matchId).toBe(MATCH);
    expect(screen.where.clubName).toBe('Sunset Padel');
    expect(screen.price).toEqual({ amount: 3800, currency: 'PLN' });
    expect(screen.mayEnter).toBe(false);
    expect(screen.mayAccept).toBe(true);
    expect(screen.mayCounter).toBe(true);
    expect(screen.settlementDeadline).toBe('2026-08-24T18:00:00Z');
    expect(screen.acceptanceGrace).toBe('2026-08-23T18:30:00Z');
  });

  it('resolves the match’s own situation through Now’s table', () => {
    // The wire embeds the spine and the situation half verbatim, so this screen and
    // the card she tapped say the same sentence about the same match. A table copied
    // into this feature is how the two come to disagree.
    const screen = toResult(resultScreen({ matchId: MATCH, situation: 'confirmResult' }));

    expect(screen.status?.line).toBe('A score is on the table — confirm it, or say what you had.');
  });

  it('loses only the sentence for a situation this build has never heard of', () => {
    const wire = resultScreen({ matchId: MATCH });
    const screen = toResult({
      ...wire,
      situation: { ...wire.situation, situation: 'reopened' as Wire['Situation'] },
    });

    expect(screen.status).toBeUndefined();
    expect(screen.ending).toBeUndefined();
    // The spine still crossed, which is the whole point of degrading rather than
    // refusing: she still knows which match this is.
    expect(screen.where.clubName).toBe('Sunset Padel');
  });

  it('counts who turned up, which the departure screen drops', () => {
    // This is the one surface where it means something: a match that has been
    // played. It is **sent** rather than derived, because *one less than the seats*
    // stops being minus one the moment a doubles match loses two people.
    const screen = toResult(
      resultScreen({ matchId: MATCH, counts: { seats: 4, paid: 4, held: 0, turned_up: 3 } }),
    );

    expect(screen.counts.turnedUp).toBe(3);
    expect(screen.counts.seats).toBe(4);
  });
});

describe('the block', () => {
  it('is empty rather than absent when nothing is on the table', () => {
    const screen = toResult(resultScreen({ matchId: MATCH, result: emptyResultBlock() }));

    expect(screen.result.agreed).toBe(false);
    expect(screen.result.proposals).toBe(0);
    expect(screen.result.score).toBeUndefined();
    expect(screen.result.proposedBy).toBeUndefined();
  });

  it('carries the score in the order it arrived, and never flips it', () => {
    const screen = toResult(resultScreen({ matchId: MATCH, result: proposed(1) }));

    expect(screen.result.score?.sides.map((side) => side.players)).toEqual([
      ['Ada', 'Kuba'],
      ['Marta', 'Ola'],
    ]);
    expect(screen.result.score?.sets).toEqual([
      { first: 6, second: 4 },
      { first: 3, second: 6 },
    ]);
  });

  it('reads the proposing side off the wire rather than off the score’s presence', () => {
    // The two are sent together, and deriving one from the other would be the phone
    // re-stating a pairing the server already makes — silently wrong the day the
    // server sends a score with no proposer.
    expect(toResult(resultScreen({ matchId: MATCH, result: proposed(0) })).result.proposedBy).toBe(
      0,
    );
    expect(toResult(resultScreen({ matchId: MATCH, result: proposed(1) })).result.proposedBy).toBe(
      1,
    );
  });
});

describe('the two endings', () => {
  it('resolves the settled one, which says nothing about anybody’s level', () => {
    const screen = toResult(resultScreen({ matchId: MATCH, situation: 'completed' }));

    expect(screen.ending?.title).toBe('Settled');
    expect(screen.ending?.lines.join(' ')).not.toMatch(/level/i);
  });

  it('resolves the unscored one, which says what the evening counted for and what it did not', () => {
    const screen = toResult(resultScreen({ matchId: MATCH, situation: 'playedNoScore' }));

    expect(screen.ending?.lines).toHaveLength(2);
    expect(screen.ending?.lines[0]).toMatch(/counts as an evening/i);
    expect(screen.ending?.lines[1]).toMatch(/level moved/i);
    expect(screen.ending?.lines[1]).toMatch(/penalised/i);
    expect(screen.ending?.lines[1]).toMatch(/friendly/i);
  });

  it('ends nothing on the situations that do not end it', () => {
    for (const situation of ['needsResult', 'confirmResult', 'forming'] as const) {
      expect(toResult(resultScreen({ matchId: MATCH, situation })).ending).toBeUndefined();
    }
  });

  it('is two rows, written out so a third is a decision somebody makes in a diff', () => {
    // The table is deliberately **partial** — thirty-four situations end nothing, and
    // writing them out as `undefined` would be thirty-four rows somebody could get
    // wrong. This is what keeps that honest.
    expect(Object.keys(ENDING_COPY).sort()).toEqual(['completed', 'playedNoScore']);
  });

  it('never resolves a key off Object.prototype', () => {
    // The table is indexed with an arbitrary string on purpose, so an ending this
    // build has never heard of resolves to nothing. Without the own-property guard,
    // `toString` resolves to a function and the block draws whatever it stringifies
    // to — the one failure worse than a missing block.
    const wire = resultScreen({ matchId: MATCH });

    expect(
      toResult({
        ...wire,
        situation: { ...wire.situation, situation: 'toString' as Wire['Situation'] },
      }).ending,
    ).toBeUndefined();
  });
});

describe('a write’s answer', () => {
  it('carries its own screen and Now’s update, in one response', () => {
    const answer = toResultAnswer(
      resultWrite(
        resultScreen({ matchId: MATCH, situation: 'confirmResult', result: proposed(0) }),
        matchCard({ matchId: MATCH, situation: 'confirmResult' }),
      ),
    );

    expect(answer.screen.result.proposedBy).toBe(0);
    expect(answer.update.kind).toBe('card');
  });
});
