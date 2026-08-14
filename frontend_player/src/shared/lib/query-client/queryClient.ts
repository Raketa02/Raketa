/**
 * The Query client's defaults — **decisions**, taken here, not library defaults
 * inherited by accident. See docs/architecture.md Part 7.
 *
 * Every value below has a reason next to it. That is the point of the file: a default
 * nobody chose is a default nobody can change safely.
 */

import { QueryClient } from '@tanstack/react-query';

import { AppError } from '@/shared/errors';

/** How many times an automatically-retryable failure is retried before it surfaces. */
const MAX_QUERY_RETRIES = 2;

/**
 * Retry only what the error model says is safe to retry unattended.
 *
 * This is the whole reason every `AppError` carries a recovery category. Without it the
 * predicate would be a growing list of status numbers, and the first endpoint whose 409
 * meant something new would be retried into a loop.
 *
 * Anything that is not an `AppError` escaped normalization — a bug in a `queryFn`, not a
 * network condition — and retrying it just runs the bug three times.
 */
function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  if (failureCount >= MAX_QUERY_RETRIES) return false;
  if (!(error instanceof AppError)) return false;
  return error.recovery === 'retryable-automatically';
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Query's own default is 0 — every mount refetches. On a phone that is the
        // player's battery and data plan. 30s is the "moderate" class: long enough that
        // navigating back to a screen does not refetch, short enough that nothing feels
        // frozen. Data classes that differ (slow reference data, live availability)
        // override it in their own feature hook, which is where that decision belongs.
        staleTime: 30_000,
        // Unused data survives five minutes of not being rendered, so returning to a
        // screen is instant while a backgrounded app does not hold a cache forever.
        gcTime: 5 * 60_000,
        retry: shouldRetryQuery,
        // Capped exponential backoff. Uncapped, the third retry on a slow connection
        // lands long after the player has given up and left the screen.
        retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 8000),
        // Both of these need their managers wired to native state to mean anything —
        // see shared/lib/platform. Wired, they are what makes returning to the app show
        // current data instead of a snapshot from before it was backgrounded.
        refetchOnWindowFocus: true,
        refetchOnReconnect: true,
        // Do not refetch a fresh query just because a second component mounted it.
        refetchOnMount: true,
        // With onlineManager wired, this pauses queries while offline instead of failing
        // them — so a reconnect resumes rather than showing an error the player has to
        // dismiss.
        networkMode: 'online',
      },
      mutations: {
        // **Mutations are never retried globally.** A mutation is retried only when the
        // endpoint is idempotent, accepts an idempotency key, or is explicitly safe to
        // repeat — and then at its own call site, with the reason stated there. A global
        // retry of "book this court" is a double booking. See Part 4.
        retry: false,
        networkMode: 'online',
      },
    },
  });
}

/**
 * The app's client. A module singleton because sign-out has to reach it from outside
 * React — clearing the cache is a privacy control, not a render concern.
 */
export const queryClient = createQueryClient();
