/**
 * **Home's Hottest groups, read** ([#800](https://github.com/Raketa02/Raketa/issues/800); the Home
 * rows mechanics §3, §13).
 *
 * | | |
 * | --- | --- |
 * | `useHottestGroups` | `GET /hottest-groups` — the row, on its own: a slow or failed read holds up nothing else on Home |
 * | `rereadHomeGroups` | the pull's — the row and the Groups list read again now, so the spinner stops on both |
 *
 * **Coming back to Home re-reads the row once its last read is older than thirty seconds** (the
 * mechanics §3, Q22) — the app's `staleTime`, so a return a moment after a read asks nothing, and the
 * group page pushed over Home is the usual way back. Foregrounding the app does the same through the
 * focus manager, on the same stale rule.
 */

import { useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { useOnReturn } from '@/shared/lib/platform';

import type { HottestGroup } from '../domain/group';
import { readHottestGroups } from '../use-cases/groupReads';

import { groupKeys } from './groupKeys';

export function useHottestGroups() {
  const client = useQueryClient();

  useOnReturn(() => {
    void client.refetchQueries({ queryKey: groupKeys.hottest(), stale: true });
  });

  return useQuery<readonly HottestGroup[], AppError>({
    queryKey: groupKeys.hottest(),
    queryFn: ({ signal }) => readHottestGroups({ signal }),
  });
}

/**
 * **Home's pull** (the mechanics §3) — the row, and the Groups list the groupless line is drawn from,
 * so a group joined on another phone takes the line away when the spinner stops.
 */
export function rereadHomeGroups(client: QueryClient): Promise<unknown> {
  return Promise.all([
    client.invalidateQueries({ queryKey: groupKeys.hottest() }),
    client.invalidateQueries({ queryKey: groupKeys.mine() }),
  ]);
}
