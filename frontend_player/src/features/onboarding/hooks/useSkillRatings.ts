/**
 * Every sport this player is rated at — the read two features now share.
 *
 * It is onboarding's because onboarding is what **produces** a rating, and it is a hook rather
 * than a second `useQuery` beside the entry gate's because the alternative is two call sites
 * agreeing by hand about one key, one `queryFn` and one mapped shape. The gate reads it to
 * decide where a launch lands; Play reads it to draw the sport chips, *"drawn only for rated
 * sports"*, which is what settles `sport_not_rated` by construction
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §2).
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
