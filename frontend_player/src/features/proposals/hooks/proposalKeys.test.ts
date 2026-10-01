/**
 * The keys nest, and that is the contract the writes rely on: an answer, a withdraw and a declared
 * intent re-read the group's root, which has to reach every sport and both kinds of that group —
 * and nothing of another group's; a changed limit re-reads every group's decks, and nothing that
 * is not a deck.
 */

import { proposalKeys } from './proposalKeys';

const GROUP = 'a0000000-0000-4000-8000-000000000005';
const OTHER = 'a0000000-0000-4000-8000-000000000011';

const startsWith = (key: readonly unknown[], prefix: readonly unknown[]) =>
  prefix.every((part, at) => key[at] === part);

describe('proposalKeys', () => {
  it('files one group’s every deck under the group’s root, and under the feature’s', () => {
    for (const key of [
      proposalKeys.deck(GROUP, 'padel', 'competitive'),
      proposalKeys.deck(GROUP, 'padel', 'forFun'),
      proposalKeys.deck(GROUP, 'tennis', 'competitive'),
    ]) {
      expect(startsWith(key, proposalKeys.group(GROUP))).toBe(true);
      expect(startsWith(key, proposalKeys.all)).toBe(true);
    }
  });

  it('keeps another group’s decks out of the root an answer re-reads', () => {
    expect(
      startsWith(proposalKeys.deck(OTHER, 'padel', 'competitive'), proposalKeys.group(GROUP)),
    ).toBe(false);
  });

  it('keys a deck by everything that changes the answer — the sport and the kind', () => {
    const keys = [
      proposalKeys.deck(GROUP, 'padel', 'competitive'),
      proposalKeys.deck(GROUP, 'padel', 'forFun'),
      proposalKeys.deck(GROUP, 'tennis', 'competitive'),
    ].map((key) => JSON.stringify(key));
    expect(new Set(keys).size).toBe(3);
  });

  it('files every group’s decks under the root a changed limit re-reads — and nothing else', () => {
    expect(startsWith(proposalKeys.deck(GROUP, 'padel', 'competitive'), proposalKeys.decks())).toBe(
      true,
    );
    expect(startsWith(proposalKeys.deck(OTHER, 'tennis', 'forFun'), proposalKeys.decks())).toBe(
      true,
    );
    expect(startsWith(proposalKeys.liveYeses(), proposalKeys.decks())).toBe(false);
    expect(startsWith(proposalKeys.gamesAndMoney(), proposalKeys.decks())).toBe(false);
  });

  it('keeps Home and a booked game out of the decks, and each booking under the bookings (#556)', () => {
    const one = proposalKeys.booking(GROUP);
    expect(startsWith(one, proposalKeys.bookings())).toBe(true);
    expect(startsWith(proposalKeys.booking(OTHER), proposalKeys.bookings())).toBe(true);
    expect(JSON.stringify(one)).not.toBe(JSON.stringify(proposalKeys.booking(OTHER)));
    expect(startsWith(proposalKeys.home(), proposalKeys.decks())).toBe(false);
    expect(startsWith(one, proposalKeys.decks())).toBe(false);
    expect(startsWith(one, proposalKeys.home())).toBe(false);
  });
});
