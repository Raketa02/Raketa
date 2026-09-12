/**
 * **The two readings of a court's seats that other surfaces key on**: which seats nobody is in,
 * and who is in the rest — by id, in the court's order, without the reader.
 *
 * Both are one definition each, because the players card, the card's spoken name, the ladder and
 * the fill all read *open* and *seated* off the same field, and two spellings of either is how a
 * three-person doubles game gets published.
 */

import type { GameSeat } from './game';
import { openSeats, seatedOthers } from './game';

const ME = 'me';
const KASIA = 'kasia';
const TOMEK = 'tomek';

/** A padel four after Marek left: three in, one open, in the court's order. */
const SHORT: readonly GameSeat[] = [
  { side: 'A', playerId: ME, nickname: 'me_' },
  { side: 'A', playerId: KASIA, nickname: 'kasia_w' },
  { side: 'B', playerId: TOMEK, nickname: 'tomek.p' },
  { side: 'B' },
];

describe('the seats nobody is in', () => {
  it('are the ones with no player, and a full court has none', () => {
    expect(openSeats(SHORT)).toEqual([{ side: 'B' }]);
    expect(openSeats(SHORT.slice(0, 3))).toEqual([]);
  });
});

/**
 * **What a fill is told about the court it completes** (#419): everybody in a seat but the reader,
 * because the reader's own seat is what the court is composed around and the builder puts it back
 * at the send — `acceptedPlayers`' shape on the challenge screen, read off a game instead.
 */
describe('everybody seated but the reader', () => {
  it('names the others in the court’s order, and skips the open seat', () => {
    expect(seatedOthers(SHORT, ME)).toEqual([KASIA, TOMEK]);
  });

  it('is nobody on a court where only the reader is left', () => {
    expect(seatedOthers([{ side: 'A', playerId: ME }, { side: 'B' }], ME)).toEqual([]);
  });
});
