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

  /**
   * Every pairing under one root (#841): a tag save marks each For-fun court's Social vibe stale at
   * once, and the list is not under it.
   */
  it('gather every pairing, and nothing else, under one root', () => {
    const under = (key: readonly unknown[], root: readonly unknown[]) =>
      root.every((part, at) => key[at] === part);

    expect(under(gameKeys.pairing('game-1'), gameKeys.pairings())).toBe(true);
    expect(under(gameKeys.pairing('game-2'), gameKeys.pairings())).toBe(true);
    expect(under(gameKeys.list(), gameKeys.pairings())).toBe(false);
  });
});
