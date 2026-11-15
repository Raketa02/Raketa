/**
 * **A people row on Home, read** ([#801](https://github.com/Raketa02/Raketa/issues/801),
 * [#802](https://github.com/Raketa02/Raketa/issues/802); the Home rows mechanics §3, §9, §13) — on
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
 */

import { useQuery, useQueryClient, type QueryKey } from '@tanstack/react-query';

import type { FriendRelation } from '@/features/friends/types';
import type { AppError } from '@/shared/errors';
import { useOnReturn } from '@/shared/lib/platform';
import { holdsPeople, type RelationMoved } from '@/shared/lib/query-client';

/** A card on a people row: whom, and where the reader stands with them. */
interface Card {
  readonly playerId: string;
  readonly relation: FriendRelation;
}

/** **The write's answer, drawn on the row as read** — the order, and everybody else, as they were. */
export function withRelation<Person extends Card>(
  people: readonly Person[],
  moved: RelationMoved<FriendRelation>,
): readonly Person[] {
  return people.map((one) =>
    one.playerId === moved.playerId ? { ...one, relation: moved.relation } : one,
  );
}

const HOLDS_STILL = holdsPeople<readonly Card[], FriendRelation>(withRelation);

export function usePeopleRow<Person extends Card>(
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
    meta: HOLDS_STILL,
  });
}
