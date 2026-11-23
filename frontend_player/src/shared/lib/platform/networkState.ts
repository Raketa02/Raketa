/**
 * `onlineManager`, wired to native connectivity.
 *
 * Query's default online check is `navigator.onLine`, which React Native either does not
 * provide or reports as a constant. Left unwired, `networkMode: 'online'` believes the
 * app is permanently online: queries fail instead of pausing, paused mutations never
 * resume, and nothing refetches when signal comes back.
 *
 * `expo-network` is the SDK-supported source. It joined package.json with this file —
 * the architecture lists it as required and not yet present, and a dependency is added
 * because code needs it, never preemptively.
 */

import { useSyncExternalStore } from 'react';

import * as Network from 'expo-network';
import { onlineManager } from '@tanstack/react-query';

/**
 * What the phone says about reaching the internet: reachability, not merely "an interface is up".
 *
 * A phone attached to a captive-portal wifi has `isConnected === true` and reaches
 * nothing. `isInternetReachable` is the honest signal; it is `null` while the platform
 * is still deciding — `undecided` here.
 *
 * - `unreachable` — no connection, or reachability known to be false. **The one offline**: the
 *   online manager pauses every query on it, and the launch does not send its check (ADR-0209 §4).
 * - `undecided` — connected, the platform still deciding. **Counted as reachable** by both: pausing
 *   every query on a maybe would strand the app at launch on connections that are perfectly fine.
 * - `reachable` — connected, and the platform says it reaches the internet.
 */
export type Reachability = 'reachable' | 'undecided' | 'unreachable';

function reachabilityOf(state: Network.NetworkState): Reachability {
  if (state.isConnected !== true || state.isInternetReachable === false) return 'unreachable';
  return state.isInternetReachable === true ? 'reachable' : 'undecided';
}

/**
 * **What the online manager was last told** — the platform's first answer, or a change since: the
 * one belief the launch and every paused query share. Forgotten when the wiring is undone.
 */
let believed: Reachability | undefined;

/** Tell the manager what the platform said — the online manager's rule — and keep it as the belief. */
function hear(state: Network.NetworkState): Reachability {
  believed = reachabilityOf(state);
  onlineManager.setOnline(believed !== 'unreachable');
  return believed;
}

/**
 * The first answer has to be asked for: the listener only fires on *change*. **A change heard while
 * it was being asked is newer than it**, so the answer is then dropped rather than set over the
 * change. A failure is not fatal: assume online and let the first request find out — and reject, so
 * a caller knows the phone said nothing.
 */
function askForTheFirstAnswer(): Promise<Reachability> {
  return Network.getNetworkStateAsync().then(
    (state) => believed ?? hear(state),
    (error: unknown) => {
      if (believed !== undefined) return believed;
      onlineManager.setOnline(true);
      throw error;
    },
  );
}

/** The first answer, as the wiring asked for it. Forgotten when the wiring is undone. */
let firstAnswer: Promise<Reachability> | undefined;

/** Called once, by the bootstrap sequence. Returns the unsubscribe for tests. */
export function wireOnlineManager(): () => void {
  believed = undefined;
  const subscription = Network.addNetworkStateListener((state) => {
    hear(state);
  });

  // Never awaited here. Kept, so the launch waits on this same answer rather than asking a second
  // time; the empty handler is only so a failure nobody has asked for yet is not unhandled.
  const answer = askForTheFirstAnswer();
  answer.catch(() => {});
  firstAnswer = answer;

  return () => {
    subscription.remove();
    firstAnswer = undefined;
    believed = undefined;
  };
}

/**
 * How long the launch waits for the platform's first answer before sending its check anyway. The
 * answer is a local read that takes milliseconds; the bound is only so a native call that never
 * settles cannot hold startup — and the splash — for ever.
 */
export const REACHABILITY_ANSWER_WITHIN_MS = 1_000;

/**
 * **The launch's one read of the phone's reachability** (ADR-0209 §4): what the online manager
 * believes, **once it has had its first answer**. Session restore reads it before its check, and
 * skips the check on `unreachable`.
 *
 * The manager's belief rather than a read of its own, because the skip holds only if the manager
 * agrees by the time the entry gate reads: the check not sent leaves nothing in the cache, so the
 * gate's own read is what says *Waiting for a connection* — and it says so only while it is paused.
 * So this waits for the answer the wiring asked for, never asks a second time, and returns the
 * belief as it stands — the first answer, or a change the platform reported since. A connection
 * that came back while the keychain was read is then sent its check, not skipped past.
 *
 * **It rejects when there is nothing to read** — the manager not wired, the phone unable to answer
 * and silent since, or no answer within `REACHABILITY_ANSWER_WITHIN_MS` — and a launch treats every
 * one of those as reachable: it sends the check.
 */
export function readReachability(): Promise<Reachability> {
  if (firstAnswer === undefined) {
    return Promise.reject(new Error('The online manager is not wired, so it believes nothing.'));
  }
  return withinTheAnswerBudget(firstAnswer).then((first) => believed ?? first);
}

function withinTheAnswerBudget(answer: Promise<Reachability>): Promise<Reachability> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const late = new Promise<never>((_, reject) => {
    timer = setTimeout(
      () => reject(new Error('The phone did not say whether it reaches the internet.')),
      REACHABILITY_ANSWER_WITHIN_MS,
    );
  });
  return Promise.race([answer, late]).finally(() => clearTimeout(timer));
}

/**
 * Whether the app believes it can reach the network **right now**, as a subscription.
 *
 * `onlineManager` is already the app's one answer to that question — it is what
 * `networkMode: 'online'` pauses on, wired above to `expo-network` rather than to
 * `navigator.onLine` — so a second source here would be a second opinion, and the two would
 * first disagree during the moment a screen is deciding what to say about the first one.
 *
 * **Its callers are not a correctness mechanism.** An act a screen will not send offline —
 * leaving a game, say — closes its control and states the reason beside it, and
 * `docs/architecture.md` Part 11 is explicit that *"button disabling is UX, not correctness"*.
 * Everything else in the app pauses and says so from `isPaused`, which needs no hook at all: a
 * paused request reports its own state.
 *
 * `useSyncExternalStore` rather than an effect and a `useState`, because the manager is an
 * external store and the first paint has to be right: an effect would render one frame of *you
 * are online* to a player who is not.
 */
export function useIsOnline(): boolean {
  return useSyncExternalStore(
    (notify) => onlineManager.subscribe(notify),
    () => onlineManager.isOnline(),
    // The server snapshot. React Native never renders on a server, and a `getServerSnapshot`
    // that disagreed with the client one would be a hydration mismatch nothing here can have —
    // it is passed so the signature is total rather than because a second environment exists.
    () => true,
  );
}
