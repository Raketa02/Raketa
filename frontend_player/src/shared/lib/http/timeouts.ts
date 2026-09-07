/**
 * The timeout policy, in one place.
 *
 * `fetch` has **no default timeout** — an unreachable host hangs until the OS gives up,
 * which on a flaky mobile network can be well over a minute of a spinner nobody can
 * cancel. Timeouts are therefore expressed as *classes*, not as a millisecond literal
 * inside a feature: a feature says what kind of work it is doing and the policy decides
 * how long that is allowed to take. See docs/architecture.md Part 4.
 *
 * Changing a number here changes it everywhere, which is the whole point — and so is
 * declining to.
 *
 * **`request` stays 15s, against a specification that asked for eight.** The Play tab's
 * three waits (the pool search, the engine fill, the send) all wanted "roughly eight
 * seconds, then an error state". They do not get it, because a search is a **recording**
 * write: every `POST /searches` appends a row to the one table the product judges itself
 * by, and the route is documented "deliberately not idempotent — two taps are two
 * searches". A client that gives up at 8s on an answer arriving at 9s therefore leaves a
 * recorded search nobody read, and its retry records a second. Shortening this number
 * does not bound a wait; it manufactures telemetry.
 *
 * The wait is bounded anyway, by a different mechanism: nothing in Play retries without
 * the player asking, so the worst case there is one timeout rather than a chain of them.
 * See https://github.com/Raketa02/Raketa/issues/239.
 */
export const TIMEOUT_MS = {
  /** An ordinary interactive read or write. Someone is looking at a spinner. */
  request: 15_000,
  /** Sending a file. Bounded by the phone's uplink, which is the slow half. */
  upload: 60_000,
  /** Fetching a file. */
  download: 60_000,
  /** Nobody is waiting. Long, but still bounded — an unbounded request leaks. */
  background: 120_000,
} as const;

export type TimeoutClass = keyof typeof TIMEOUT_MS;
