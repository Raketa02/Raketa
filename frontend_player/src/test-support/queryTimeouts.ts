/**
 * Query's garbage-collection timers, unref'd — for the test process only.
 *
 * ## What this fixes
 *
 * `pnpm test` printed "A worker process has failed to exit gracefully" on every run (#29).
 * The cause is a live handle, not a failing assertion: **Query's `gcTime` is five minutes**
 * (a deliberate app default — see `shared/lib/query-client`), and every query and mutation
 * that loses its last observer schedules a real `setTimeout(…, 300_000)`. A jest worker
 * exits when its event loop empties; a pending five-minute timer means it never does, so
 * jest force-exits it after the grace period and says so.
 *
 * ## Why teardown cannot fix it
 *
 * `queryClient.clear()` in `afterEach` does not cancel those timers. `authFlow.test.tsx`
 * ended with **ten** of them pending, and both halves of that were measured rather than
 * assumed — destroying every mutation before clearing removed six and left four:
 *
 * - **Six mutations.** Clearing removes a mutation from the mutation cache without clearing
 *   its gc timeout, so the timer outlives the cache entry. `queryTimeouts.test.ts` pins
 *   this, so a future Query release that starts cancelling them tells us rather than us
 *   noticing in a year.
 * - **Four orphans.** Sign-out is a system operation that calls `queryClient.clear()` from
 *   app code *while the tree is still mounted* (`shared/lib/auth/session.ts`). Those entries
 *   leave the cache with their observers still attached, so the later unmount schedules gc
 *   on an object no cache holds — and no subsequent `clear()` can reach it. Skipping the
 *   sign-out tests is what takes the remaining four to zero.
 *
 * The second half is unreachable through any public API, which is why the fix is a timer
 * provider and not a teardown hook: a teardown hook can only ever fix the first six.
 *
 * Unref'ing is the answer the warning itself suggests. It changes no timing: the timers
 * still fire, they simply stop being a reason for the process to stay alive. Only Query's
 * timers are affected — an app timer that leaks still holds the worker open, which is the
 * point of not reaching for `--forceExit`.
 *
 * ## Why only one suite ever showed it
 *
 * The router-driven suites are clean because `expo-router/testing-library` installs jest's
 * fake timers, which makes the same gc timers inert. `authFlow.test.tsx` renders screens
 * directly, on real timers, so it was the only suite left holding a real handle.
 *
 * That is also why the original bisection could not find a culprit: jest runs a **single**
 * test file in-band, with no worker at all, so a one-suite run cannot produce the warning
 * whatever it leaks — and `--detectOpenHandles` forces the same in-band run.
 *
 * Not app code — nothing under `src/` imports this, so Metro never bundles it.
 */

import { timeoutManager } from '@tanstack/query-core';

/**
 * A timer handle Node keeps a reference to, versus the number React Native returns.
 * Under jest's fake timers the handle is neither, so the capability is tested, not assumed.
 */
function unref<T>(handle: T): T {
  const candidate = handle as { unref?: () => void };
  if (typeof candidate?.unref === 'function') candidate.unref();
  return handle;
}

/** Point Query's timers at unref'd ones. Called once, from `jest.setup.js`. */
export function installUnrefTimeouts(): void {
  timeoutManager.setTimeoutProvider({
    setTimeout: (callback, delay) => unref(setTimeout(callback, delay)),
    clearTimeout: (handle) => clearTimeout(handle),
    setInterval: (callback, delay) => unref(setInterval(callback, delay)),
    clearInterval: (handle) => clearInterval(handle),
  });
}
