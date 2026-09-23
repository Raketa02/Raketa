/**
 * Two keys under one root: the list, and a pairing **per game** — the second because the pairing
 * is a route of its own with an id in the path, where a game is looked up inside the list.
 */

import { gameKeys } from './gameKeys';

describe('the keys', () => {
  it('nest under the feature root, so a sign-out clears them together', () => {
    expect(gameKeys.list()).toEqual(['games', 'list']);
    expect(gameKeys.pairing('game-1')).toEqual(['games', 'pairing', 'game-1']);
  });

  /** Every parameter that changes the response is in the key, and the id is the only one. */
  it('key each game’s pairing apart', () => {
    expect(gameKeys.pairing('game-1')).not.toEqual(gameKeys.pairing('game-2'));
  });
});
