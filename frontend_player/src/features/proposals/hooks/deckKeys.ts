/**
 * **The proposals feature's query keys** — one factory, so every read and every write names the
 * same entries.
 *
 * Under one group, the deck for a sport and a kind: an answer, a withdraw and a declared intent
 * re-read the group's root, which is every sport and both kinds — a yes moves the badge, which
 * spans the segments, and a declaration decides which segments there are.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { GameKind } from '../domain/vocabulary';

export const deckKeys = {
  all: ['proposals'] as const,
  /** Every deck read for one group — the root an answer re-reads. */
  group: (groupId: string) => [...deckKeys.all, 'deck', groupId] as const,
  /** One group's deck, for one sport and one kind. */
  deck: (groupId: string, sport: Sport, kind: GameKind) =>
    [...deckKeys.group(groupId), sport, kind] as const,
};
