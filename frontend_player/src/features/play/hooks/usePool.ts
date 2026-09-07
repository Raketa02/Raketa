/**
 * The pool's two acts against the record — **one refreshes it in place, one replaces it with
 * another.**
 *
 * | | |
 * | --- | --- |
 * | `useReadSearchBack` | `GET /searches/{id}` — the same id, the same key, live gates |
 * | `useTakeRung` | `POST /searches` — **a new id**, a new key, and a list that supersedes |
 *
 * Both are mutations and neither is a query, which is the same test `useBuilder` applies and
 * not the verb each one wears. The re-read is a `GET`, but what makes it a mutation here is
 * that its **answer is a cache effect**: it writes the whole `SearchRecord` back under the key
 * the record already lives at, and there is no second entry for a screen to subscribe to. A
 * `useQuery` on that key would need a fetcher, and `useBuilder`'s own subscription to the same
 * key deliberately has none — *"a search record is written, never fetched"* — so two hooks with
 * two fetchers over one key is the one shape that cannot be made coherent.
 *
 * ## Neither retries, and that is the tab's posture rather than a choice made here
 *
 * Mutations ship `retry: false`. For the rung that is `POST /searches`' own rule — *"two taps
 * are two searches"*, so an automatic retry is a second recorded search nobody asked for. For
 * the re-read it is *"nothing in Play retries without the player asking"*: a `GET` records
 * nothing, so the argument is purely about the affordance, and an automatic retry the player
 * cannot see is a manual retry they cannot reach — roughly thirty-one seconds of it
 * (`hooks/searchKeys.ts`).
 *
 * **And the retry belongs to the act that failed.** A record id exists in both cases, but they
 * are not the same act: re-reading is *the-record* and re-running is *the-search*, and a
 * *Try again* that re-ran the search would mint a new id and orphan the line-up bound to the
 * old one — which `POST /forecasts` answers with `404 search_not_found`, one code for four
 * cases (`domain/retryTarget`). So the pool's re-read gets the control, and taking a rung
 * keeps its own.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { SearchRecord } from '../domain/lineup';
import { readSearchBack } from '../use-cases/readSearchBack';
import { takeRung, type TakeRungAsk } from '../use-cases/takeRung';
import type { SearchOutcome } from '../use-cases/findAGame';

import { searchKeys } from './searchKeys';

/**
 * Re-read the search this pool was opened on, **in place**.
 *
 * The cache effect is the whole act: the entry is replaced under the same key, so every screen
 * subscribed to it — the court one push below, and this list — redraws off one write. The
 * record that goes back is the held one with its answer refreshed, because the origin and the
 * court have no representation on the wire (`use-cases/readSearchBack`).
 */
export function useReadSearchBack() {
  const client = useQueryClient();

  return useMutation<SearchRecord, AppError, SearchRecord>({
    mutationFn: (held) => readSearchBack(held),
    onSuccess: (record) => {
      client.setQueryData<SearchRecord>(searchKeys.detail(record.searchId), record);
    },
  });
}

/**
 * Take a rung — and land on a **different record**, under a different key.
 *
 * The old entry is left exactly where it is rather than removed. It is what the line-up
 * already on court is bound to and what the court one push below is drawing from, and there is
 * no way back to the strict list only in the sense that this **screen** does not offer one
 * ([#223](https://github.com/Raketa02/Raketa/issues/223) §6): a player holding two lists would
 * be diffing them to find the people that differ, which is the engine's job.
 */
export function useTakeRung() {
  const client = useQueryClient();

  return useMutation<SearchOutcome, AppError, TakeRungAsk>({
    mutationFn: takeRung,
    onSuccess: ({ record }) => {
      client.setQueryData<SearchRecord>(searchKeys.detail(record.searchId), record);
    },
  });
}
