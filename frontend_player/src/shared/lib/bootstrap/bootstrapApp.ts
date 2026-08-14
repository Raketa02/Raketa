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
 *  -> load fonts                              <- here
 *  -> hide the splash screen                  <- BootstrapGate
 *  -> render
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

import { loadEnv } from "@/shared/config/env";
import { wireHttpCredentials } from "@/shared/lib/auth";
import { wireFocusManager, wireOnlineManager } from "@/shared/lib/platform";

import { loadFonts } from "./fonts";

export interface BootstrapSteps {
  /** Throws when the build's public config is missing or malformed. */
  readonly validateConfig: () => void;
  /** Points TanStack Query's focus and online managers at native state. */
  readonly wirePlatformManagers: () => void;
  /** Hands the HTTP client its credential adapter, before any request can be made. */
  readonly wireCredentials: () => void;
  /**
   * Reads the keychain and asks the server whether what it found is still a session.
   *
   * Supplied by the root layout rather than defaulted here: it belongs to the auth
   * feature, and `shared/` may never import a feature.
   */
  readonly restoreSession: () => Promise<void>;
  readonly loadFonts: () => Promise<void>;
}

/**
 * The steps `shared/` can supply on its own. The root layout spreads this and adds
 * `restoreSession`, which is the one step that has to come from a feature.
 */
export const sharedBootstrapSteps = {
  validateConfig: loadEnv,
  wirePlatformManagers: () => {
    wireFocusManager();
    wireOnlineManager();
  },
  wireCredentials: wireHttpCredentials,
  loadFonts,
} as const satisfies Omit<BootstrapSteps, "restoreSession">;

export async function bootstrapApp(steps: BootstrapSteps): Promise<void> {
  steps.validateConfig();
  steps.wirePlatformManagers();
  steps.wireCredentials();

  // Before the fonts, because it is the step that decides which tree renders. A launch
  // that painted the unauthenticated tree and then corrected itself is the flash the
  // whole sequence exists to prevent.
  await steps.restoreSession();

  await steps.loadFonts();
}
