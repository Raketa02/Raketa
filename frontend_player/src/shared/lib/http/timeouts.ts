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
