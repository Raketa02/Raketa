/**
 * **The Rankings route's params** ([#775](https://github.com/Raketa02/Raketa/issues/775)) — the sport
 * the page opens on: the trophy's, or the one a pass returns to. A route param is untrusted input
 * (`docs/architecture.md`), so it is checked here before anything reads it, and **anything that is
 * not one sport this build knows is no sport** — the page then opens as the trophy with none would.
 */

import { z } from 'zod';

import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

const RankingsParamsSchema = z.object({ sport: z.enum(SPORTS) });

export interface RankingsParams {
  readonly sport?: Sport;
}

export function parseRankingsParams(params: Readonly<Record<string, unknown>>): RankingsParams {
  const parsed = RankingsParamsSchema.safeParse(params);
  return parsed.success ? { sport: parsed.data.sport } : {};
}
