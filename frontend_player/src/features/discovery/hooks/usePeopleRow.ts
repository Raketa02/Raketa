/**
 * **A people row on Home, read** ([#801](https://github.com/Raketa02/Raketa/issues/801),
 * [#802](https://github.com/Raketa02/Raketa/issues/802); the Home rows mechanics §3, §13) — on its
 * own, so a slow or failed read holds up nothing else on Home.
 *
 * - **Coming back to Home re-reads it once its last read is older than thirty seconds** — the app's
 *   `staleTime`, as Hottest groups does; foregrounding does the same through the focus manager.
 * - **One tap moves a person everywhere**: the read declares `LISTS_PEOPLE`, so every friend write
 *   and every block — wherever it is made — reads the row again.
 */

import { useQuery, useQueryClient, type QueryKey } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import { useOnReturn } from '@/shared/lib/platform';
import { LISTS_PEOPLE } from '@/shared/lib/query-client';

export function usePeopleRow<Person>(
  queryKey: QueryKey,
  read: (signal: AbortSignal) => Promise<readonly Person[]>,
) {
  const client = useQueryClient();

  useOnReturn(() => {
    void client.refetchQueries({ queryKey, stale: true });
  });

  return useQuery<readonly Person[], AppError>({
    queryKey,
    queryFn: ({ signal }) => read(signal),
    meta: LISTS_PEOPLE,
  });
}
