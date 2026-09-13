/**
 * The room's own folds — what it hands the plan card about its court, and where a page backward
 * starts from.
 *
 * The line-up is the one this ticket adds: the room knows who is in and whether the court has its
 * game, the sport knows how many seats it takes, and the card wants the two folded into one fact
 * it can read without knowing either.
 */

import { earlierThan, lineUpOf } from './room';

const PADEL = 4;

describe('the line-up the card is handed', () => {
  /**
   * Two of a padel four are in and the court has no game: still filling, and the numbers ride on
   * that arm because that is the arm with a line to say them on (ADR-0164 §5).
   */
  it('is still filling while the room has no game, with who is in against the court', () => {
    expect(lineUpOf({ members: [{}, {}] }, PADEL)).toEqual({
      complete: false,
      members: 2,
      seats: 4,
    });
    expect(lineUpOf({ members: [{}, {}, {}] }, PADEL)).toEqual({
      complete: false,
      members: 3,
      seats: 4,
    });
  });

  /**
   * **The game is the fact, never the count** (ADR-0165 §1: *has this court become a game* is the
   * line-up having completed). A game a seat has since been left open on is three of four with a
   * game, and its line-up is complete — the lock is offered and the server's refusal is a sentence.
   */
  it('is complete the moment the room has its game, whatever the count', () => {
    expect(lineUpOf({ gameId: 'g', members: [{}, {}, {}, {}] }, PADEL)).toEqual({ complete: true });
    expect(lineUpOf({ gameId: 'g', members: [{}, {}, {}] }, PADEL)).toEqual({ complete: true });
  });
});

describe('paging backward', () => {
  it('asks for what is before the oldest thing held, and stops at the beginning', () => {
    expect(earlierThan(7)).toBe(7);
    expect(earlierThan(1)).toBeUndefined();
    expect(earlierThan(undefined)).toBeUndefined();
  });
});
