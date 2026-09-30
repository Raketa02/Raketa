/**
 * The deck's keys nest, and that is the contract the writes rely on: an answer, a withdraw and a
 * declared intent re-read the group's root, which has to reach every sport and both kinds of that
 * group — and nothing of another group's.
 */

import { deckKeys } from './deckKeys';

const GROUP = 'a0000000-0000-4000-8000-000000000005';
const OTHER = 'a0000000-0000-4000-8000-000000000011';

const startsWith = (key: readonly unknown[], prefix: readonly unknown[]) =>
  prefix.every((part, at) => key[at] === part);

describe('deckKeys', () => {
  it('files one group’s every deck under the group’s root, and under the feature’s', () => {
    for (const key of [
      deckKeys.deck(GROUP, 'padel', 'competitive'),
      deckKeys.deck(GROUP, 'padel', 'forFun'),
      deckKeys.deck(GROUP, 'tennis', 'competitive'),
    ]) {
      expect(startsWith(key, deckKeys.group(GROUP))).toBe(true);
      expect(startsWith(key, deckKeys.all)).toBe(true);
    }
  });

  it('keeps another group’s decks out of the root an answer re-reads', () => {
    expect(startsWith(deckKeys.deck(OTHER, 'padel', 'competitive'), deckKeys.group(GROUP))).toBe(
      false,
    );
  });

  it('keys a deck by everything that changes the answer — the sport and the kind', () => {
    const keys = [
      deckKeys.deck(GROUP, 'padel', 'competitive'),
      deckKeys.deck(GROUP, 'padel', 'forFun'),
      deckKeys.deck(GROUP, 'tennis', 'competitive'),
    ].map((key) => JSON.stringify(key));
    expect(new Set(keys).size).toBe(3);
  });
});
