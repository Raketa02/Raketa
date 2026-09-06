/**
 * The wire boundary, and the one asymmetry it holds: **vocabulary degrades in place, structure
 * is refused whole.**
 *
 * The list is *"your games, newest arrangement first"*, and a client that dropped a row because
 * a code on it had grown a fifth value would be the same class of lie as a read-back that got
 * shorter. So a standing this build cannot read leaves a game in the list with a named gap, and
 * only a sport with no score shape or a side with no place on a court takes one out.
 */

import type { Wire } from '@/test-support/transport';

import { toGame, toGames, toStateResultRequest } from './gameMappers';

const READ_AT = '2026-09-05T09:00:00Z';

function wireGame(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: 'game-1',
    challenge_id: 'ask-1',
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: '2026-09-01T18:00:00Z',
    seats: [
      { side: 'A', player_id: 'me' },
      { side: 'B', player_id: 'them' },
    ],
    proposals: [],
    ...over,
  };
}

/** One side's score on the table, with the two deadlines the screens read off it. */
function wireProposal(side: 'A' | 'B'): Wire['StandingProposalSchema'] {
  return {
    side,
    proposed_by: side === 'A' ? 'me' : 'them',
    score: { sets: [{ a: 4, b: 6 }] },
    proposed_at: '2026-09-04T20:12:00Z',
    answer_by: '2026-09-05T20:12:00Z',
    settles_at: '2026-09-05T02:12:00Z',
  };
}

describe('one game off the wire', () => {
  it('carries the instant the list was folded against, so a countdown cannot disagree', () => {
    expect(toGame(wireGame(), READ_AT)?.readAt).toBe(READ_AT);
  });

  it('collapses every null to absent, so no screen has two spellings of nothing', () => {
    const game = toGame(
      wireGame({ played_at: null, entry_closes_at: null, score: null, outcome: null }),
      READ_AT,
    );

    expect(game).toMatchObject({ playedAt: undefined, score: undefined, outcome: undefined });
  });

  it('reads the scores on the table whole, deadlines included', () => {
    const game = toGame(
      wireGame({
        standing: 'AWAITING_ANSWER',
        played_at: '2026-09-04T20:12:00Z',
        proposals: [wireProposal('B')],
      }),
      READ_AT,
    );

    expect(game?.proposals).toEqual([
      {
        side: 'B',
        proposedBy: 'them',
        score: { sets: [{ a: 4, b: 6 }] },
        answerBy: '2026-09-05T20:12:00Z',
        settlesAt: '2026-09-05T02:12:00Z',
      },
    ]);
  });

  /**
   * Both of them, in the server's order — *side A's first and never in the order they arrived*,
   * because the order of the two acts is a fact about who reached their phone first.
   */
  it('keeps both scores of a disagreement, in the order they were served', () => {
    const game = toGame(
      wireGame({
        standing: 'AWAITING_ANSWER',
        played_at: '2026-09-04T20:12:00Z',
        proposals: [wireProposal('A'), wireProposal('B')],
      }),
      READ_AT,
    );

    expect(game?.proposals.map((one) => one.side)).toEqual(['A', 'B']);
  });

  /**
   * Two of the wire's four acceptance fields, on the rule the proposal already follows: what a
   * screen reads and nothing else. `agreed_by` names a person on a court where nobody is named.
   */
  it('reads an agreement as the side whose score it settles, and when', () => {
    const game = toGame(
      wireGame({
        standing: 'AWAITING_ANSWER',
        played_at: '2026-09-04T20:12:00Z',
        proposals: [wireProposal('A'), wireProposal('B')],
        acceptance: {
          agreed_by: 'them',
          of_side: 'A',
          agreed_at: '2026-09-04T21:00:00Z',
          settles_at: '2026-09-05T02:12:00Z',
        },
      }),
      READ_AT,
    );

    expect(game?.acceptance).toEqual({ ofSide: 'A', settlesAt: '2026-09-05T02:12:00Z' });
  });

  it('leaves an agreement absent when the response carried none', () => {
    expect(toGame(wireGame({ acceptance: null }), READ_AT)?.acceptance).toBeUndefined();
  });
});

describe('a code this build has never seen', () => {
  it('leaves a standing absent and the game in the list', () => {
    const games = toGames({
      read_at: READ_AT,
      // @ts-expect-error — a sixth standing is exactly what an old build meets on a real phone.
      games: [wireGame({ standing: 'ABANDONED' })],
    });

    expect(games).toHaveLength(1);
    expect(games[0]?.standing).toBeUndefined();
  });

  it('leaves a kind absent and every other sentence on the screen standing', () => {
    // @ts-expect-error — same case, one vocabulary over.
    const game = toGame(wireGame({ kind: 'LADDER' }), READ_AT);

    expect(game?.kind).toBeUndefined();
    expect(game?.sport).toBe('padel');
  });

  it('drops a game whose sport has no score shape, because there is no instrument to draw', () => {
    // @ts-expect-error — a fifth sport is a release, and this build is the one before it.
    expect(toGames({ read_at: READ_AT, games: [wireGame({ sport: 'PICKLEBALL' })] })).toEqual([]);
  });

  it('drops a game whose court it cannot place somebody on', () => {
    const games = toGames({
      read_at: READ_AT,
      // @ts-expect-error — a third side would be a different court, not a wider one.
      games: [wireGame({ seats: [{ side: 'C', player_id: 'me' }] })],
    });

    expect(games).toEqual([]);
  });

  /**
   * Structure again, and for a sharper reason than the seat's: dropping one score of two would
   * leave a lone proposal on screen — a different story about the same game, told confidently.
   */
  it('drops a game carrying a score it cannot attribute to a side', () => {
    const games = toGames({
      read_at: READ_AT,
      games: [
        wireGame({
          standing: 'AWAITING_ANSWER',
          played_at: '2026-09-04T20:12:00Z',
          // @ts-expect-error — a third side is the same redesign, one field over.
          proposals: [wireProposal('A'), { ...wireProposal('B'), side: 'C' }],
        }),
      ],
    });

    expect(games).toEqual([]);
  });

  it('drops a game whose agreement names a side it cannot read', () => {
    const games = toGames({
      read_at: READ_AT,
      games: [
        wireGame({
          standing: 'AWAITING_ANSWER',
          played_at: '2026-09-04T20:12:00Z',
          proposals: [wireProposal('A')],
          acceptance: {
            agreed_by: 'them',
            // @ts-expect-error — same redesign; an agreement with nobody settles nothing.
            of_side: 'C',
            agreed_at: '2026-09-04T21:00:00Z',
            settles_at: '2026-09-05T02:12:00Z',
          },
        }),
      ],
    });

    expect(games).toEqual([]);
  });
});

describe('the score going back', () => {
  it('is the sets and nothing else — no act name, because the record decides which', () => {
    expect(
      toStateResultRequest({
        sets: [
          { a: 6, b: 4 },
          { a: 6, b: 2 },
        ],
      }),
    ).toEqual({
      score: {
        sets: [
          { a: 6, b: 4 },
          { a: 6, b: 2 },
        ],
      },
    });
  });
});
