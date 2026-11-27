/**
 * **When a read counts as finished** (PRD #867, [#871](https://github.com/Raketa02/Raketa/issues/871);
 * the loading shimmer log §5, Q13) — what a screen built from several reads waits on before it
 * reveals (`shared/ui`'s `useRevealParts`). A read has finished once any of these has happened:
 *
 * - **it landed** — it holds data, whatever it is doing now;
 * - **it was refused** — Query gave up on it;
 * - **it paused for a connection** — the phone is offline, and the screen says so;
 * - **it failed once and started retrying.** One failing read must not hold a screen through its
 *   backoff: what it draws while it retries is its own section's to say.
 *
 * **Read off Query's own state, never mirrored into a store** (the player app's state table). The
 * hooks here watch the cache and draw again only when their answer changes — a read refetched in
 * the background, a pull, or another read moving in the cache draws nothing new — so a screen may ask
 * them about every read it waits on and pay for the moment each one ends, and nothing else.
 */

import {
  notifyManager,
  useQueryClient,
  type QueryClient,
  type QueryKey,
  type QueryState,
} from '@tanstack/react-query';
import { useCallback, useSyncExternalStore } from 'react';

/** The parts of a read's state that say whether it has finished. */
export type ReadEnding = Pick<QueryState, 'data' | 'status' | 'fetchStatus' | 'fetchFailureCount'>;

/**
 * **Whether a read has finished** — landed, refused, paused for a connection, or failed once and
 * retrying. A read nobody has asked for (`undefined`), one on its way, and one waiting for what it is
 * to be asked with (`skipToken`, idle) have not.
 */
export function readHasFinished(read: ReadEnding | undefined): boolean {
  if (read === undefined) return false;
  return (
    read.data !== undefined ||
    read.status === 'error' ||
    read.fetchStatus === 'paused' ||
    read.fetchFailureCount > 0
  );
}

/**
 * **How far a read has come** ([#875](https://github.com/Raketa02/Raketa/issues/875)): `reading` —
 * out, or not yet asked, with nothing to show; `landed` — it holds data, whatever it is doing now;
 * `ended` — finished with nothing to show: refused, paused for a connection, or failed once and
 * retrying. A part whose read has *ended* reveals what it draws then, the failure or the offline
 * note, which is not its content — so when the read sets out again, *Try again* or the connection
 * back, it is `reading` once more and the part's skeleton stands again (`shared/ui`'s `Reveal`).
 */
export type ReadStage = 'reading' | 'landed' | 'ended';

export function readStage(read: ReadEnding | undefined): ReadStage {
  if (read?.data !== undefined) return 'landed';
  return readHasFinished(read) ? 'ended' : 'reading';
}

/**
 * **An answer read off the query cache**, drawn again only when it changes. `answer` must give a
 * value compared by identity — a flag, a word — never a new object or list on every call.
 *
 * The cache's every move is told through Query's own batching, as Query's hooks are, so the answer is
 * looked at once the cache has settled, never while another component draws.
 */
export function useQueryCacheAnswer<Answer extends boolean | number | string | undefined>(
  answer: (client: QueryClient) => Answer,
): Answer {
  const client = useQueryClient();
  const cache = client.getQueryCache();
  const subscribe = useCallback(
    (onChange: () => void) => cache.subscribe(notifyManager.batchCalls(onChange)),
    [cache],
  );
  const read = () => answer(client);
  return useSyncExternalStore(subscribe, read, read);
}

/** **Whether the read under this key has finished** — see the module note. */
export function useReadFinished(queryKey: QueryKey): boolean {
  return useQueryCacheAnswer((client) => readHasFinished(client.getQueryState(queryKey)));
}
