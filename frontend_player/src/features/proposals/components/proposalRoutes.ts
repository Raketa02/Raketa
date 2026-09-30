/**
 * **Where a game's details live** — pushed over the group's page from its Games deck, under Play,
 * so the Play column stays lit and *back* is the deck. Named here, beside the screens that reach
 * it, and read by the route file too: a path spelled twice is the one that goes stale.
 *
 * The sport and the kind ride with the ids because the details draw the card **the deck dealt** —
 * the read for this group, this sport and this kind — and nothing else knows which read that was.
 * All four are checked where the route reads them (`schemas/gameDetailsParams`).
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { GameKind } from '../domain/vocabulary';

export function gameRoute(groupId: string, proposalId: string, sport: Sport, kind: GameKind) {
  return {
    pathname: '/play/group/[groupId]/game/[proposalId]',
    params: { groupId, proposalId, sport, kind },
  } as const;
}
