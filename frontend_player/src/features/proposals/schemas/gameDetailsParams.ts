/**
 * **A game's details route params, checked before anything trusts them** — a route param is input
 * from outside the app, and the screen draws the card the deck dealt for exactly this group, sport
 * and kind, so each of the four has to be one this build can read.
 */

import { z } from 'zod';

import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

import type { GameKind } from '../domain/vocabulary';

const GAME_KINDS = ['competitive', 'forFun'] as const satisfies readonly GameKind[];

const GameDetailsParams = z.object({
  groupId: z.string().uuid(),
  proposalId: z.string().uuid(),
  sport: z.enum(SPORTS),
  kind: z.enum(GAME_KINDS),
});

export interface GameDetailsRoute {
  readonly groupId: string;
  readonly proposalId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
}

/** The four, or `undefined` for params this app cannot read. */
export function parseGameDetailsParams(params: unknown): GameDetailsRoute | undefined {
  const parsed = GameDetailsParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}
