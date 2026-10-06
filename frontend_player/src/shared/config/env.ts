/**
 * Public runtime configuration — read once, validated once, at launch.
 *
 * NOTHING HERE IS SECRET. Every `EXPO_PUBLIC_*` value is inlined into the JavaScript
 * bundle and can be read out of a shipped app; these are *config*. A secret a mobile
 * client appears to need is a design error and belongs behind the backend.
 * See docs/architecture.md Part 14.
 *
 * Validation happens in the bootstrap sequence rather than lazily at the first read, so
 * a missing or malformed value fails at launch with the variable's name on screen —
 * not three screens deep as `fetch("undefined/api/v1/…")`.
 */

import { z } from 'zod';

import { LINK_DOMAIN_RULE, readLinkDomain } from './appLinks';

/**
 * The four environments, named identically by all three apps.
 *
 * `local` is a developer's own machine and is the only one that runs today.
 * `development` and `staging` are defined and validated but **not provisioned** — no
 * domain is registered — and `production` does not exist yet either. Selecting one is a
 * startup failure rather than a silent fallback to whatever happens to be reachable.
 *
 * `local` is the name that was missing, and its absence was the bug: a developer's own
 * laptop was called `development`, which is the name that will mean a shared remote
 * deployment. The two would then be indistinguishable in a log line.
 */
export const ENVIRONMENTS = ['local', 'development', 'staging', 'production'] as const;

export type AppEnvironment = (typeof ENVIRONMENTS)[number];

/** Spelled once, for the refusal message and for the environment template. */
const ENVIRONMENT_NAMES = ENVIRONMENTS.join(', ');

/**
 * An absolute HTTP(S) URL.
 *
 * `.url()` alone is not enough: WHATWG parsing accepts `localhost:8000` as a URL whose
 * *protocol* is `localhost:`, and that is precisely what someone types. It would pass
 * validation and then fail on every request.
 *
 * Named rather than inlined so the cross-field rule below can ask whether the field itself
 * already refused the value.
 */
const httpUrlField = z
  .string()
  .url()
  .refine((value) => /^https?:\/\//i.test(value), {
    message: 'must start with http:// or https://',
  });

/**
 * The scheme the API URL must use, per environment — `null` where either is legitimate.
 *
 * This is the **public-network** form of the rule, and it is the strict one: the API is reached
 * from a phone, over the internet, so a deployed environment carrying it in the clear is a
 * session and a bearer token on someone's café Wi-Fi. `https://` there is not a
 * deployment-topology preference, it is the security invariant.
 *
 * `local` is `null`, and that is the correction #102 asked for. The rule used to require
 * `http://` on the reasoning that `local` is "a laptop, a LAN IP or a tunnel" — but
 * `expo start --tunnel`, `cloudflared` and `tailscale funnel` all hand back `https://`, so
 * the one case a tunnel exists for (a physical phone that cannot reach the laptop's LAN IP)
 * was refused at launch. Nothing about `local` is protected by forbidding TLS on it.
 *
 * Written out per environment rather than as `env === 'local' ? … : …` so that a fifth
 * environment fails to compile until somebody decides how it is reached.
 */
const REQUIRED_SCHEME: Readonly<Record<AppEnvironment, 'https://' | null>> = {
  local: null,
  development: 'https://',
  staging: 'https://',
  production: 'https://',
};

const EnvFields = z.object({
  EXPO_PUBLIC_API_URL: httpUrlField,
  /**
   * The message is replaced rather than left to zod, whose `invalid_enum_value` text ends
   * `received '…'`. Config lands in logs and crash reports, and a variable's value is
   * never something a refusal echoes back — the same rule the URL follows.
   */
  EXPO_PUBLIC_ENV: z.enum(ENVIRONMENTS, {
    errorMap: () => ({ message: `must be one of ${ENVIRONMENT_NAMES}` }),
  }),
  /**
   * **The web domain the app's links live on** — `raketa.app`, bare — or nothing, which is every
   * environment today ([#520](https://github.com/Raketa02/Raketa/issues/520), ADR-0187 §7). While it
   * is empty the links open the app by its own scheme only. `appLinks.ts` reads it for this file and
   * for `app.config.ts` alike, once each, in one wording — which, like every refusal here, never
   * echoes the value.
   */
  EXPO_PUBLIC_LINK_DOMAIN: z
    .string()
    .optional()
    .transform((value, ctx) => {
      try {
        return readLinkDomain(value);
      } catch {
        ctx.addIssue({ code: z.ZodIssueCode.custom, message: LINK_DOMAIN_RULE });
        return z.NEVER;
      }
    }),
});

/**
 * The variables the scheme rule governs — each one a URL a phone reaches over the internet. One
 * since the feature-flag datafile's host left with the flags (#576); a list still, so a second URL
 * joins the rule by being named here.
 */
const SCHEMED_URLS = ['EXPO_PUBLIC_API_URL'] as const;

/**
 * The scheme rule is a claim about a URL and the environment *together*, so it is checked on
 * the object rather than on the field — once per URL, by one loop, so the guard below cannot be
 * written for one URL and forgotten for the next.
 *
 * **It stays silent when the field itself already refused the value**, and that guard is
 * measured rather than assumed. The docstring here used to claim zod "runs it only once
 * both fields have parsed"; that was false. A failing `.url()` or `.refine()` leaves zod's
 * result *dirty* rather than aborting it, so this refinement still ran over the rejected
 * string — `localhost:8000` was reported both as a malformed URL and as a scheme mismatch,
 * two complaints for one typo, the second of them naming the environment rather than the
 * missing scheme. Re-running the field is what makes "a malformed URL is reported as a
 * malformed URL" true instead of merely intended.
 *
 * The issue is attached to the URL — that is the value that has to change — and names
 * `EXPO_PUBLIC_ENV` as the reason. An environment name is not a secret and is already on every
 * log record; it is the *reason* here, never the offending value.
 */
const EnvSchema = EnvFields.superRefine((env, ctx) => {
  const scheme = REQUIRED_SCHEME[env.EXPO_PUBLIC_ENV];

  if (scheme === null) return;

  for (const variable of SCHEMED_URLS) {
    const url = env[variable];

    if (!httpUrlField.safeParse(url).success) continue;

    if (!url.toLowerCase().startsWith(scheme)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: [variable],
        message: `must start with ${scheme} when EXPO_PUBLIC_ENV is ${env.EXPO_PUBLIC_ENV}`,
      });
    }
  }
});

export interface Env {
  /** FastAPI base URL. On a physical device this is a LAN IP or tunnel — a phone's
   *  `localhost` is the phone. Either scheme in `local`, `https://` everywhere else. */
  readonly apiUrl: string;
  readonly environment: AppEnvironment;
  /** The web domain the app's links live on, bare — `null` while none is set, which is today. */
  readonly linkDomain: string | null;
}

/**
 * Startup configuration is unusable rather than merely wrong, so it gets its own error
 * type: it is raised before the session, the HTTP client or the normalized `AppError`
 * family exist, and no recovery category applies to it.
 */
export class ConfigError extends Error {
  override readonly name = 'ConfigError';
}

/** The raw shape a build hands us: every variable present-or-absent, always a string. */
export type RawEnv = Readonly<Partial<Record<keyof z.infer<typeof EnvFields>, string>>>;

/**
 * Pure: validate a raw environment. Throws `ConfigError` naming the offending variables
 * and why — **never their values**, because config lands in logs and crash reports and a
 * URL can carry credentials.
 */
export function parseEnv(raw: RawEnv): Env {
  const result = EnvSchema.safeParse(raw);

  if (!result.success) {
    const problems = result.error.issues
      .map((issue) => `${issue.path.join('.') || '(root)'}: ${issue.message}`)
      .join('; ');

    throw new ConfigError(
      `Invalid app configuration — ${problems}. Copy .env.example to .env.local and fill it in.`,
    );
  }

  return {
    apiUrl: result.data.EXPO_PUBLIC_API_URL,
    environment: result.data.EXPO_PUBLIC_ENV,
    linkDomain: result.data.EXPO_PUBLIC_LINK_DOMAIN,
  };
}

/**
 * Expo's Babel plugin substitutes `EXPO_PUBLIC_*` at **statically written member
 * accesses only** — `process.env[name]` is `undefined` in a release bundle. Every
 * variable therefore has to be spelled out here, which is also why this is the one
 * function in the app that mentions `process.env`.
 */
function readRawEnv(): RawEnv {
  return {
    EXPO_PUBLIC_API_URL: process.env.EXPO_PUBLIC_API_URL,
    EXPO_PUBLIC_ENV: process.env.EXPO_PUBLIC_ENV,
    EXPO_PUBLIC_LINK_DOMAIN: process.env.EXPO_PUBLIC_LINK_DOMAIN,
  };
}

let loaded: Env | undefined;

/** Validate and memoize. Called by the bootstrap sequence; safe to call again. */
export function loadEnv(): Env {
  loaded ??= parseEnv(readRawEnv());
  return loaded;
}

/**
 * The validated config. Throws if bootstrap has not run — which is a wiring bug, not a
 * user-facing failure, and should never be caught and papered over.
 */
export function getEnv(): Env {
  if (loaded === undefined) {
    throw new ConfigError('Config read before bootstrap validated it. Call loadEnv() first.');
  }
  return loaded;
}
