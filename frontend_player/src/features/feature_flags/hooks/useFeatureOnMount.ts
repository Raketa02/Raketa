/**
 * **A gate: is this feature enabled, asked once, when the screen mounts** (ADR-0206 §7).
 *
 * The answer is fixed for the life of the screen. A datafile that arrives while it is up — at the
 * next foreground, say — changes nothing on it; the next mount reads the new answer. So a player
 * in the middle of something never has the screen swapped out from under them, and a merged
 * toggle takes effect cleanly, at a moment the player chose.
 *
 * **It reads the cache and subscribes to nothing.** A subscription could only deliver an answer
 * this hook has promised to ignore, and an observer on the player's own read would refetch
 * `/users/me` on every mount of every gated screen. The two datafile reads are kept current by
 * `useFeatureDatafile`, not here.
 *
 * Whatever is not in hand yet when the screen mounts is answered by the next rung: a datafile
 * still in flight means the saved one, and none saved means the code default.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { currentUserQuery, type AuthenticatedUser } from '@/features/auth/types';
import { getEnv } from '@/shared/config/env';
import { appBuild } from '@/shared/lib/platform';

import type { EvaluationContext, FeatureKey } from '../domain/featureFlags';
import { isFeatureEnabled } from '../use-cases/isFeatureEnabled';

import { freshDatafileQuery, savedDatafileQuery } from './datafileQueries';

export function useFeatureOnMount(feature: FeatureKey): boolean {
  const client = useQueryClient();

  const [enabled] = useState(() => {
    const { environment } = getEnv();
    const player = client.getQueryData(currentUserQuery().queryKey);

    return isFeatureEnabled(feature, {
      fresh: client.getQueryData(freshDatafileQuery(environment).queryKey),
      cached: client.getQueryData(savedDatafileQuery(environment).queryKey),
      context: evaluationContextFor(player),
    });
  });

  return enabled;
}

/**
 * The attributes, as the flags repo spells them (§8): who, and which build on which platform —
 * and nobody, with no signed-in player to bucket. No tester mark: the account carries none (§9).
 */
function evaluationContextFor(
  player: AuthenticatedUser | undefined,
): EvaluationContext | undefined {
  if (player === undefined) return undefined;
  return { playerId: player.id, ...appBuild() };
}
