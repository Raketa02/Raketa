/**
 * **The two readings of a court's seats that other surfaces key on**: which seats nobody is in,
 * and who is in the rest — by id, in the court's order, without the reader.
 *
 * Both are one definition each, because the players card, the card's spoken name, the ladder and
 * the fill all read *open* and *seated* off the same field, and two spellings of either is how a
 * three-person doubles game gets published.
 */

import type { GameSeat } from './game';
import { openSeats } from './game';

const ME = 'me';
const KASIA = 'kasia';
const TOMEK = 'tomek';

/** A padel four after Marek left: three in, one open, in the court's order. */
const SHORT: readonly GameSeat[] = [
  { side: 'A', playerId: ME, name: 'me_' },
  { side: 'A', playerId: KASIA, name: 'kasia_w' },
  { side: 'B', playerId: TOMEK, name: 'tomek.p' },
  { side: 'B' },
];

describe('the seats nobody is in', () => {
  it('are the ones with no player, and a full court has none', () => {
    expect(openSeats(SHORT)).toEqual([{ side: 'B' }]);
    expect(openSeats(SHORT.slice(0, 3))).toEqual([]);
  });
});
