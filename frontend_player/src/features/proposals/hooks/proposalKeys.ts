/**
 * **The proposals feature's query keys** — one factory, so every read and every write names the
 * same entries.
 *
 * Under one group, the deck for a sport and a kind: an answer, a withdraw and a declared intent
 * re-read the group's root, which is every sport and both kinds — a yes moves the badge, which
 * spans the segments, and a declaration decides which segments there are. **Every group's decks
 * sit under one root too**, because Games & money bounds them all: a changed limit re-reads it.
 *
 * Beside the decks, the player's own two reads (#554): their live yeses, which every answer and
 * withdraw changes, and Games & money.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { GameKind } from '../domain/vocabulary';

export const proposalKeys = {
  all: ['proposals'] as const,
  /** Every deck read, of every group — the root a changed limit re-reads. */
  decks: () => [...proposalKeys.all, 'deck'] as const,
  /** Every deck read for one group — the root an answer re-reads. */
  group: (groupId: string) => [...proposalKeys.decks(), groupId] as const,
  /** One group's deck, for one sport and one kind. */
  deck: (groupId: string, sport: Sport, kind: GameKind) =>
    [...proposalKeys.group(groupId), sport, kind] as const,
  /** `GET /players/me/live-yeses` — every yes on a game still filling, across groups. */
  liveYeses: () => [...proposalKeys.all, 'live-yeses'] as const,
  /** `GET /players/me/payments-to-confirm` — the reader's refused shares, waiting for them (#555). */
  paymentsToConfirm: () => [...proposalKeys.all, 'payments-to-confirm'] as const,
  /** `GET /players/me/games-and-money` — the two limits. */
  gamesAndMoney: () => [...proposalKeys.all, 'games-and-money'] as const,
};
