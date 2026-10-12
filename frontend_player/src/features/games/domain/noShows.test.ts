/**
 * **Who a player may mark as not coming** ([#560](https://github.com/Raketa02/Raketa/issues/560);
 * the Games & Fill in mechanics §15.3). Where the result of a booked game is entered, each other
 * player on the court has a row, and every row can be marked — nobody at the club checks anybody
 * in (ADR-0195). The rows go once a score is entered, and for a player who was marked themselves:
 * their answer is the dispute.
 */

import type { Game, NoShowReport } from './game';
import { noShowRows } from './noShows';

const ME = 'me-1111-4444-8888-000000000001';
const PARTNER = 'partner-11-4444-8888-000000002';
const KUBA = 'kuba-11111-4444-8888-00000003';
const INES = 'ines-11111-4444-8888-00000004';

function game(over: Partial<Game> = {}): Game {
  return {
    gameId: 'game-1111-4444-8888-00000000001',
    sport: 'padel',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    seats: [
      { side: 'A', playerId: ME, name: 'Ada Lis' },
      { side: 'A', playerId: PARTNER, name: 'Piotr Sowa' },
      { side: 'B', playerId: KUBA, name: 'Kuba Nowak' },
      { side: 'B', playerId: INES },
    ],
    plannedAt: '2026-09-01T18:00:00Z',
    entryClosesAt: '2026-09-09T18:00:00Z',
    proposals: [],
    noShows: [],
    readAt: '2026-09-05T09:00:00Z',
    ...over,
  };
}

function report(playerId: string): NoShowReport {
  return {
    playerId,
    reportedAt: '2026-09-04T20:00:00Z',
    disputeBy: '2026-09-05T20:00:00Z',
  };
}

describe('the didn’t-come rows where a booked game’s result is entered', () => {
  it('lists every other player on the court, in its order, named whole', () => {
    expect(noShowRows(game(), ME)).toStrictEqual([
      { playerId: PARTNER, who: { kind: 'player', name: 'Piotr Sowa' } },
      { playerId: KUBA, who: { kind: 'player', name: 'Kuba Nowak' } },
      { playerId: INES, who: { kind: 'unknown' } },
    ]);
  });

  it('goes on listing the players nobody has marked while a report’s day runs', () => {
    const reported = game({
      standing: 'NO_SHOW_REPORTED',
      entryClosesAt: undefined,
      noShows: [report(KUBA)],
    });

    expect(noShowRows(reported, ME).map((row) => row.playerId)).toEqual([PARTNER, INES]);
  });

  it('lists nobody for a player who was marked — theirs is the dispute', () => {
    const reported = game({
      standing: 'NO_SHOW_REPORTED',
      entryClosesAt: undefined,
      noShows: [report(ME)],
    });

    expect(noShowRows(reported, ME)).toEqual([]);
  });

  it('lists nobody once a score is entered, nor on a game that has ended', () => {
    const played = { playedAt: '2026-09-04T20:12:00Z', entryClosesAt: undefined } as const;

    expect(noShowRows(game({ ...played, standing: 'AWAITING_ANSWER' }), ME)).toEqual([]);
    expect(noShowRows(game({ ...played, standing: 'CONFIRMED' }), ME)).toEqual([]);
    expect(noShowRows(game({ standing: 'PLAYED_NO_SCORE' }), ME)).toEqual([]);
    expect(noShowRows(game({ standing: 'NO_SHOW', noShows: [report(KUBA)] }), ME)).toEqual([]);
  });

  /**
   * **A For fun game asks nothing about its score** (#654), and somebody can still not come to it:
   * the rows are offered there too until its score is up, until attendance replaces them (#658).
   */
  it('lists the others on a For fun game too, until its score is up', () => {
    expect(noShowRows(game({ kind: 'FRIENDLY' }), ME).map((row) => row.playerId)).toContain(KUBA);
    expect(
      noShowRows(
        game({ kind: 'FRIENDLY', standing: 'CONFIRMED', score: { sets: [{ a: 6, b: 4 }] } }),
        ME,
      ),
    ).toEqual([]);
  });

  it('lists nobody on a court with a seat open, nor for somebody not on it', () => {
    const short = game({
      seats: [
        { side: 'A', playerId: ME, name: 'Ada Lis' },
        { side: 'B', playerId: KUBA, name: 'Kuba Nowak' },
        { side: 'B' },
      ],
    });

    expect(noShowRows(short, ME)).toEqual([]);
    expect(noShowRows(game(), 'stranger-1-4444-8888-00000009')).toEqual([]);
  });
});
