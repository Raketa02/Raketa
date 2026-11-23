/**
 * The one ordered startup sequence. Nothing renders a route tree before it resolves.
 *
 * The order in docs/architecture.md Part 3 is:
 *
 *     initialise crash/error reporting        <- a later slice (observability)
 *  -> read + validate public runtime config   <- here
 *  -> wire focusManager / onlineManager       <- here
 *  -> read credentials from SecureStore       <- here, via restoreSession
 *  -> restore + validate the session          <- here
 *  -> start reading the install referrer       <- here, not awaited (#756)
 *  -> load fonts                              <- here
 *  -> render, underneath the drawn splash     <- LaunchGate
 *
 * **It runs behind the drawn splash, and nothing waits on it to show one** (ADR-0209 §2). It no
 * longer ends by hiding a native splash: the launch gate lets the OS launch window go on the drawn
 * splash's first layout, before this has done anything, and fades the splash when the first screen
 * is ready.
 *
 * Only the steps whose code exists are implemented; the rest are inserted here as their
 * slices land, so there is never a second place that runs work at launch.
 *
 * Config is validated *first* and synchronously: everything after it — the API base URL
 * the session validation calls, the environment observability reports under — reads a
 * value that has to be trustworthy by then. A bad config that surfaced after a font
 * download is a bad config that wasted a launch.
 *
 * **Every step is injected, and none is optional.** A step with a default no-op is a step
 * that can be forgotten silently; making the object exhaustive means adding a slice
 * fails to compile until its step is wired in.
 */

import { loadEnv } from '@/shared/config/env';
import { wireFocusManager, wireOnlineManager } from '@/shared/lib/platform';

import { loadFonts } from './fonts';

export interface BootstrapSteps {
  /** Throws when the build's public config is missing or malformed. */
  readonly validateConfig: () => void;
  /** Points TanStack Query's focus and online managers at native state. */
  readonly wirePlatformManagers: () => void;
  /**
   * Hands the HTTP client its credential adapter, before any request can be made.
   *
   * Supplied by the root layout: the adapter now carries the token rotation, and the
   * rotation's wire call belongs to the auth feature.
   */
  readonly wireCredentials: () => void;
  /**
   * Reads the keychain and asks the server whether what it found is still a session.
   *
   * Supplied by the root layout rather than defaulted here: it belongs to the auth
   * feature, and `shared/` may never import a feature.
   */
  readonly restoreSession: () => Promise<void>;
  /**
   * **Starts** reading the link an Android install carried, once on the app's first launch, and
   * holds it as if it had been tapped (#756). Supplied by the root layout — links are a feature's —
   * and **never awaited**: the answer is Google Play's, another app's, and the splash does not wait
   * on it. It never throws.
   */
  readonly readInstallReferrer: () => void;
  readonly loadFonts: () => Promise<void>;
}

/**
 * The steps `shared/` can supply on its own. The root layout spreads this and adds the
 * three that have to come from a feature.
 */
export const sharedBootstrapSteps = {
  validateConfig: loadEnv,
  wirePlatformManagers: () => {
    wireFocusManager();
    wireOnlineManager();
  },
  loadFonts,
} as const satisfies Omit<
  BootstrapSteps,
  'restoreSession' | 'wireCredentials' | 'readInstallReferrer'
>;

export async function bootstrapApp(steps: BootstrapSteps): Promise<void> {
  steps.validateConfig();
  steps.wirePlatformManagers();
  steps.wireCredentials();

  // Before the fonts, because it is the step that decides which tree renders. A launch
  // that painted the unauthenticated tree and then corrected itself is the flash the
  // whole sequence exists to prevent.
  await steps.restoreSession();

  // After the session, so a link it holds is held against the session the launch settled on.
  steps.readInstallReferrer();

  await steps.loadFonts();
}
