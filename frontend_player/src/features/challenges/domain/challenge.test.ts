/**
 * The pair rule, read from the client's side — **the naming a refusal refuses to do.**
 *
 * What is asserted is the set of claims a build session could quietly undo: an ended challenge
 * releases the pair, a seat that declined or lapsed releases one person out of a challenge
 * that still stands, and the organiser is never the answer to *who are you already playing*.
 */

import type { Challenge, ChallengeSeat } from './challenge';
import { challengeStands, pairAlreadyPlaying, playersStillIn } from './challenge';
import { STANDINGS, type Standing } from './standing';

const ME = 'me';
const BEA = 'bea';
const CYRYL = 'cyryl';

function challenge(standing: Standing, seats: readonly ChallengeSeat[]): Challenge {
  return { challengeId: 'c1', organiserId: ME, standing, seats };
}

/** A live singles game between the two of us: my seat accepted from birth, theirs waiting. */
const WAITING_ON_BEA = challenge('AWAITING_ANSWERS', [
  { playerId: ME, answer: 'ACCEPTED' },
  { playerId: BEA },
]);

describe('which challenges still hold a pair', () => {
  it('counts the three live standings and neither of the two endings', () => {
    const stands = STANDINGS.filter((standing) => challengeStands(challenge(standing, [])));

    expect(stands).toEqual(['AWAITING_ANSWERS', 'ON', 'LINE_UP_INCOMPLETE']);
  });

  it('empties an ended challenge, so the pair releases with it', () => {
    const declined = challenge('DECLINED', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'DECLINED' },
    ]);

    expect(playersStillIn(declined)).toEqual([]);
  });

  /**
   * A decline and a lapse both open the seat, and **the challenge can stand without them**: a
   * padel four where one person said no is `LINE_UP_INCOMPLETE`, and that one person is a
   * stranger again while the other two are not.
   */
  it('drops the seat that said no from a challenge that still stands', () => {
    const short = challenge('LINE_UP_INCOMPLETE', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: CYRYL, answer: 'DECLINED' },
      {},
    ]);

    expect(playersStillIn(short)).toEqual([ME, BEA]);
  });

  it('drops the seat whose day ran out for the same reason, and it is not a decline', () => {
    const lapsed = challenge('LINE_UP_INCOMPLETE', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: CYRYL, answer: 'LAPSED' },
      {},
    ]);

    expect(playersStillIn(lapsed)).toEqual([ME, BEA]);
  });
});

describe('who on this court you already have a game with', () => {
  it('names the invitee an open challenge of yours still holds', () => {
    expect(pairAlreadyPlaying([WAITING_ON_BEA], [BEA, CYRYL])).toBe(BEA);
  });

  /** In seat order, because §21's sentence names one person and the court has an order. */
  it('names the first of them in seat order', () => {
    const withCyryl = challenge('ON', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: CYRYL, answer: 'ACCEPTED' },
    ]);

    expect(pairAlreadyPlaying([WAITING_ON_BEA, withCyryl], [CYRYL, BEA])).toBe(CYRYL);
  });

  /** The organiser holds a seat in every challenge of their own, so they are never the answer. */
  it('is asked without the organiser, so their own seat names nobody', () => {
    expect(pairAlreadyPlaying([WAITING_ON_BEA], [CYRYL])).toBeUndefined();
  });

  /**
   * The refusal is about **any** pair on the court, so the game in the way can be between two
   * invitees — and that one is not the organiser's to read. Nothing is named, and the screen
   * says the nameless thing rather than guessing.
   */
  it('names nobody when the game in the way is not one of yours', () => {
    expect(pairAlreadyPlaying([], [BEA, CYRYL])).toBeUndefined();
  });

  it('names nobody out of a challenge that has ended', () => {
    const over = challenge('LAPSED', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'LAPSED' },
    ]);

    expect(pairAlreadyPlaying([over], [BEA])).toBeUndefined();
  });
});
