/**
 * Which foot the radar's record sheet draws — the standing relation between the reader and the
 * person on the card, folded once (ADR-0174 §4, `the-radar.md` §5).
 */

import { standingRelation } from './standingRelation';

const COURT = { challengeId: 'c1' };
const NOBODY = { saidYes: false, matched: false, court: undefined } as const;

describe('the standing relation', () => {
  it('is open — the two buttons — where nothing stands between the two', () => {
    expect(standingRelation(NOBODY)).toEqual({ kind: 'open' });
  });

  /** A pass the reader gave earlier is not a relation the client can see: the two buttons, and a yes lifts it. */
  it('is a liker where the row carries the admitting code', () => {
    expect(standingRelation({ ...NOBODY, inclusionReason: 'INTEREST_LIFT' })).toEqual({
      kind: 'liker',
    });
  });

  it('is said-yes where the reader has a live yes towards them', () => {
    expect(standingRelation({ ...NOBODY, saidYes: true })).toEqual({ kind: 'said-yes' });
  });

  it('is matched where their yes came back, whatever else is true', () => {
    expect(standingRelation({ ...NOBODY, matched: true })).toEqual({ kind: 'matched' });
    expect(
      standingRelation({
        saidYes: true,
        matched: true,
        court: COURT,
        inclusionReason: 'INTEREST_LIFT',
      }),
    ).toEqual({ kind: 'matched' });
  });

  /** A court between them outranks the reader's own yes and their yes: the game is where a rematch is arranged. */
  it('is the court where the two share one, over a yes either way, and hands the court back', () => {
    expect(standingRelation({ ...NOBODY, court: COURT })).toEqual({ kind: 'court', court: COURT });
    expect(standingRelation({ ...NOBODY, court: COURT, saidYes: true })).toEqual({
      kind: 'court',
      court: COURT,
    });
    expect(standingRelation({ ...NOBODY, court: COURT, inclusionReason: 'INTEREST_LIFT' })).toEqual(
      { kind: 'court', court: COURT },
    );
  });

  /** Both interest facts at once is a mutual the lists have not caught up with; the other person's decision wins, as on the builder's card. */
  it('reads a liker over the reader’s own yes', () => {
    expect(
      standingRelation({ ...NOBODY, saidYes: true, inclusionReason: 'INTEREST_LIFT' }),
    ).toEqual({ kind: 'liker' });
  });
});
