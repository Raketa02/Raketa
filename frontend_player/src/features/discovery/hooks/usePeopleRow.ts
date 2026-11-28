/**
 * **A people row on Home, read** ([#801](https://github.com/Rakieta02/Rakieta/issues/801),
 * [#802](https://github.com/Rakieta02/Rakieta/issues/802); the Home rows mechanics §3, §9, §13) — on
 * its own, so a slow or failed read holds up nothing else on Home.
 *
 * - **Coming back to Home re-reads it once its last read is older than thirty seconds** — the app's
 *   `staleTime`, as Hottest groups does; foregrounding does the same through the focus manager.
 * - **It holds still under the thumb** (`holdsPeople`): a friend write — wherever it is made — draws
 *   its answer on the person's card where it stands, and marks the row stale rather than reading it
 *   again now. The row is worked out again on every read (§9.1), and asking a fresh match makes them
 *   a gap the next fresh match takes the place of; read at the tap, the card would leave under the
 *   thumb. **The next read** — a return, a pull, foregrounding — **moves them**.
 * - **A block re-reads it at once**, and so does a refusal that is the state moving: those cards leave.
 * - **Its total moves with its reads and nothing else** ([#822](https://github.com/Rakieta02/Rakieta/issues/822);
 *   ADR-0205 §6): the line's count and *See all N ›* are the server's, so a friend write drawn on a
 *   card leaves them as read, and the next read brings the new figure. Nothing polls for it.
 */

import { queryOptions, useQuery, useQueryClient, type QueryKey } from '@tanstack/react-query';

import type { FriendRelation } from '@/features/friends/types';
import type { AppError } from '@/shared/errors';
import { useOnReturn } from '@/shared/lib/platform';
import { holdsPeople, type RelationMoved } from '@/shared/lib/query-client';

import { withRelation, type PeopleRow } from '../domain/peopleRow';

/** A card on a people row: whom, and where the reader stands with them. */
interface Card {
  readonly playerId: string;
  readonly relation: FriendRelation;
}

/** The write's answer drawn on the row as read — the domain's rule (`withRelation`). */
const HOLDS_STILL = holdsPeople<PeopleRow<Card>, FriendRelation>(
  (row, moved: RelationMoved<FriendRelation>) => withRelation(row, moved.playerId, moved.relation),
);

/**
 * **A row's read, as one definition** — its key, its fetch and the hold under a friend write: what
 * the row's hook observes and Home's warm-up sets out before Home is drawn (#874), so the two cannot
 * differ in anything Home would ask again for.
 */
export function peopleRowRead<Person extends Card>(
  queryKey: QueryKey,
  read: (signal: AbortSignal) => Promise<PeopleRow<Person>>,
) {
  return queryOptions<PeopleRow<Person>, AppError>({
    queryKey,
    queryFn: ({ signal }) => read(signal),
    meta: HOLDS_STILL,
  });
}

export function usePeopleRow<Person extends Card>(row: ReturnType<typeof peopleRowRead<Person>>) {
  const client = useQueryClient();

  useOnReturn(() => {
    void client.refetchQueries({ queryKey: row.queryKey, stale: true });
  });

  return useQuery(row);
}
