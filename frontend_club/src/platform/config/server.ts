/**
 * Server-only configuration — read once, validated once, at server start.
 *
 * **Everything here is private to the server tier.** The FastAPI origin, the environment
 * and the session cookie policy are read by BFF route handlers (`src/app/api/*`) and by
 * Server Components, and never reach the browser. `import "server-only"` makes that a
 * build error rather than a convention: a Client Component that imports this module fails
 * to compile, instead of shipping and reading `undefined` at runtime. That is §19.1's MUST
 * — "any module capable of reading tokens, secrets or the FastAPI base URL MUST be
 * impossible to import into client bundles" — and ADR-0007's central rule.
 *
 * The public counterpart is `./public`, which holds only values that are *meant* to be in
 * the bundle. Two schemas, never one (§20.1).
 *
 * Validation happens at server start rather than lazily at the first read, so a missing or
 * malformed value fails at boot with the variable's name in the log — not on the first
 * request that happens to touch a rare screen (§20.2). `src/instrumentation.ts` is what
 * makes "at boot" true.
 */

import "server-only";

import { z } from "zod";

import {
  environmentField,
  httpUrlField,
  parseOrThrow,
  requireScheme,
  type AppEnvironment,
} from "./environment";

/**
 * `APP_ENV`, not `NEXT_PUBLIC_ENV`, and the name is load-bearing twice over. It is the
 * same variable the backend reads, so the two agree by spelling; and it is unprefixed, so
 * Next cannot inline it into the client bundle. The environment is deliberately *not*
 * mirrored into a public variable — a second copy is a second thing to drift, and the
 * badge reads this one through a Server Component instead.
 */
const ServerFields = z.object({
  APP_ENV: environmentField,

  /**
   * The FastAPI origin. **Never** rename this to `NEXT_PUBLIC_*` (ADR-0007, §4.1): the
   * browser must only ever talk to this app's own `/api/*`, and a public FastAPI origin
   * is an invitation to call it directly and bypass the BFF's session and CSRF handling.
   *
   * **Validated for shape and no further — it deliberately carries no scheme rule.** This
   * is a *server-to-server* address: the club's own server tier calls it, and a browser
   * never learns it. In a deployed environment that address is commonly cluster-internal —
   * `http://backend.svc.cluster.local:8000` — which never crosses a public network and is
   * entirely legitimate. #96 implemented the rule as its AC specified and reported that it
   * refuses exactly that; #99 settles it. Whether this hop is encrypted is a
   * deployment-topology question the app cannot answer, not a security invariant it can
   * assert. See docs/environments.md.
   */
  BACKEND_API_URL: httpUrlField,

  /**
   * The name of the httpOnly session cookie the BFF writes. Constrained to an RFC 6265
   * cookie token: a name containing a space or a separator produces a `Set-Cookie` header
   * that browsers silently drop, which presents as "login does nothing".
   */
  SESSION_COOKIE_NAME: z
    .string()
    .min(1)
    .regex(/^[A-Za-z0-9!#$%&'*+\-.^_`|~]+$/, {
      message: "must be a cookie name — letters, digits and !#$%&'*+-.^_`|~ only",
    }),

  /**
   * The club app's own public origin. Safe to expose, and it *is* exposed — `./public`
   * validates its shape for the browser. It is re-read here because only the server knows
   * the environment, and therefore only the server can enforce the scheme rule on it.
   *
   * **This is the one URL here the public-network scheme rule applies to**, and it is what
   * carries the unprovisioned-environment refusal now that `BACKEND_API_URL` does not: a
   * `local` configuration promoted to `staging` by changing one variable still fails at
   * start, because a browser origin of `http://localhost:3000` is not a deployed one.
   */
  NEXT_PUBLIC_APP_URL: httpUrlField,

  /**
   * **Refused, not ignored.** The `Secure` flag is derived from `APP_ENV` below and can no
   * longer be set by hand — that independence was the footgun: a cookie policy that says
   * `false` in a deployed environment is a session transmitted in clear, and it looks
   * deliberate because somebody typed it.
   *
   * Silently ignoring a stale `SESSION_COOKIE_SECURE=false` would leave an operator
   * believing a security control is in effect that nothing reads. A variable that looks
   * like it controls security and does not is worse than one that is absent, so its
   * presence stops the server rather than being dropped.
   */
  SESSION_COOKIE_SECURE: z.undefined({
    // No trailing period: `parseOrThrow` appends the remedy sentence after it.
    invalid_type_error:
      "is no longer read — the Secure flag is derived from APP_ENV (false only in local), so remove it from the environment",
  }),
});

const ServerSchema = ServerFields.superRefine((raw, ctx) => {
  // Only the browser-facing origin. `BACKEND_API_URL` is server-to-server — see its field.
  requireScheme(ctx, raw.APP_ENV, "NEXT_PUBLIC_APP_URL", raw.NEXT_PUBLIC_APP_URL);
});

/** The session cookie policy. `secure` is derived, never configured. */
export interface SessionCookieConfig {
  readonly name: string;
  /**
   * Derived from the environment: `false` only in `local`, where there is no TLS on
   * `http://localhost`. Every deployed environment gets `true` — which is also why the
   * scheme rule and this flag can never disagree, since both are read off `APP_ENV`.
   */
  readonly secure: boolean;
}

export interface ServerConfig {
  readonly environment: AppEnvironment;
  /** FastAPI base URL. Server-only, and server-to-server: either scheme, any environment. */
  readonly backendApiUrl: string;
  /** This app's own origin, as the server knows it. */
  readonly appUrl: string;
  readonly session: SessionCookieConfig;
}

/** The raw shape a deployment hands us: every variable present-or-absent, always a string. */
export type RawServerEnv = Readonly<Partial<Record<keyof z.infer<typeof ServerFields>, string>>>;

const REMEDY = "Copy .env.example to .env.local and fill it in.";

/**
 * Pure: validate a raw environment and map it onto the app's configuration. Exported so it
 * can be tested without a process, and so the mapping — including the derived `secure`
 * flag — is exercised rather than inferred.
 */
export function parseServerConfig(raw: RawServerEnv): ServerConfig {
  const parsed = parseOrThrow(ServerSchema, raw, REMEDY);

  return {
    environment: parsed.APP_ENV,
    backendApiUrl: parsed.BACKEND_API_URL,
    appUrl: parsed.NEXT_PUBLIC_APP_URL,
    session: {
      name: parsed.SESSION_COOKIE_NAME,
      // Derived, not configured. `local` is the only environment without TLS.
      secure: parsed.APP_ENV !== "local",
    },
  };
}

/**
 * Every variable is spelled out at a statically written member access. Next substitutes
 * `process.env.X` at build time for public variables, and a computed `process.env[name]`
 * is not substituted at all — so the indirection that looks tidier is the one that returns
 * `undefined` in a built app.
 *
 * This function and `./public`'s twin are the only places in the app that mention
 * `process.env`; a lint rule holds that.
 */
function readRawServerEnv(): RawServerEnv {
  return {
    APP_ENV: process.env.APP_ENV,
    BACKEND_API_URL: process.env.BACKEND_API_URL,
    SESSION_COOKIE_NAME: process.env.SESSION_COOKIE_NAME,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    SESSION_COOKIE_SECURE: process.env.SESSION_COOKIE_SECURE,
  };
}

let loaded: ServerConfig | undefined;

/**
 * The validated server configuration. Memoized: the schema runs once per server process,
 * not once per request.
 *
 * Safe to call from `instrumentation.ts` at boot and from a route handler afterwards — the
 * first call validates and every later one reads the same object.
 */
export function getServerConfig(): ServerConfig {
  loaded ??= parseServerConfig(readRawServerEnv());
  return loaded;
}
