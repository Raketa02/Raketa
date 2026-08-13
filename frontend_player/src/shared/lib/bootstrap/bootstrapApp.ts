/**
 * The one ordered startup sequence. Nothing renders a route tree before it resolves.
 *
 * The order in docs/architecture.md Part 3 is:
 *
 *     initialise crash/error reporting        <- a later slice (observability)
 *  -> read + validate public runtime config   <- here
 *  -> wire focusManager / onlineManager       <- a later slice (Query + expo-network)
 *  -> read credentials from SecureStore       <- a later slice (auth)
 *  -> restore + validate the session          <- a later slice (auth)
 *  -> load fonts                              <- here
 *  -> hide the splash screen                  <- BootstrapGate
 *  -> render
 *
 * Only the steps whose code exists are implemented; the rest are inserted here as their
 * slices land, so there is never a second place that runs work at launch.
 *
 * Config is validated *first* and synchronously: everything after it — the API base URL
 * the session validation would call, the environment observability reports under —
 * reads a value that has to be trustworthy by then. A bad config that surfaced after a
 * font download is a bad config that wasted a launch.
 */

import { loadEnv } from "@/shared/config/env";

import { loadFonts } from "./fonts";

export interface BootstrapSteps {
  /** Throws when the build's public config is missing or malformed. */
  readonly validateConfig: () => void;
  readonly loadFonts: () => Promise<void>;
}

const defaultSteps: BootstrapSteps = {
  validateConfig: loadEnv,
  loadFonts,
};

export async function bootstrapApp(steps: BootstrapSteps = defaultSteps): Promise<void> {
  steps.validateConfig();
  await steps.loadFonts();
}
