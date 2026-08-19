/**
 * Next's server-start hook — the club app's equivalent of a bootstrap sequence.
 *
 * `register()` runs once per server process, before the first request is served. Reading
 * the configuration here is what makes "**fails loudly at server start**" true: without
 * it, a missing `BACKEND_API_URL`, or a `staging` deployment still pointed at
 * `http://localhost:8000`, would be discovered by whichever user first opened a screen
 * that happened to call the backend (§20.2).
 *
 * Only the server tier is validated here. The public schema is validated where it is read:
 * its values are inlined at *build* time, so a running server process is not what proves
 * them present.
 *
 * There is deliberately no `NEXT_RUNTIME === "nodejs"` guard. The usual reason for one is
 * Node-only APIs, and there are none here — this is zod over `process.env`, which the edge
 * runtime has too. Guarding would mean an edge deployment starts happily with configuration
 * the node tier would have refused, which is the failure this file exists to prevent.
 */

import { getServerConfig } from "./platform/config/server";

export async function register(): Promise<void> {
  // Throws ConfigError, naming the offending variable and never its value. An unstarted
  // server is the correct outcome — the alternative is one that serves errors it cannot
  // explain.
  getServerConfig();
}
