/**
 * Every sport this player is rated at — the read two features now share.
 *
 * It is onboarding's because onboarding is what **produces** a rating, and it is a hook rather
 * than a `useQuery` per caller because the alternative is several call sites agreeing by hand
 * about one key, one `queryFn` and one mapped shape. A group's page reads it to draw the sport
 * chip — *drawn only for rated sports* — and to decide whether its reader meets the level door
 * (ADR-0200 §2, §4); the You tab and the passport read it for their cards. **The entry gate no
 * longer does** (#730): a rating routes no launch.
 *
 * **Ordinary defaults, deliberately.** `searchKeys.ts` lists the ratings behind the sport chips
 * among the reads that *do* refetch: nothing in Play background-refetches a **ranked list**,
 * because foregrounding would reorder the pool under the player's finger — a chip row is not
 * one, and a sport rated on another device should appear.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { SkillRating } from '../domain/SkillRating';
import { listRatings } from '../use-cases/listRatings';

import { onboardingKeys } from './onboardingKeys';

export function useSkillRatings() {
  return useQuery<readonly SkillRating[], AppError>({
    queryKey: onboardingKeys.ratings(),
    queryFn: ({ signal }) => listRatings({ signal }),
  });
}
