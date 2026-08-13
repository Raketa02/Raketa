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

import { z } from "zod";

const EnvSchema = z.object({
  /**
   * `.url()` alone is not enough: WHATWG parsing accepts `localhost:8000` as a URL whose
   * *protocol* is `localhost:`, and that is precisely what someone types. It would pass
   * validation and then fail on every request.
   */
  EXPO_PUBLIC_API_URL: z
    .string()
    .url()
    .refine((value) => /^https?:\/\//i.test(value), {
      message: "must start with http:// or https://",
    }),
  EXPO_PUBLIC_ENV: z.enum(["development", "staging", "production"]),
});

export type AppEnvironment = z.infer<typeof EnvSchema>["EXPO_PUBLIC_ENV"];

export interface Env {
  /** FastAPI base URL. On a physical device this is a LAN IP or tunnel — a phone's
   *  `localhost` is the phone. */
  readonly apiUrl: string;
  readonly environment: AppEnvironment;
}

/**
 * Startup configuration is unusable rather than merely wrong, so it gets its own error
 * type: it is raised before the session, the HTTP client or the normalized `AppError`
 * family exist, and no recovery category applies to it.
 */
export class ConfigError extends Error {
  override readonly name = "ConfigError";
}

/** The raw shape a build hands us: every variable present-or-absent, always a string. */
export type RawEnv = Readonly<Partial<Record<keyof z.infer<typeof EnvSchema>, string>>>;

/**
 * Pure: validate a raw environment. Throws `ConfigError` naming the offending variables
 * and why — **never their values**, because config lands in logs and crash reports and a
 * URL can carry credentials.
 */
export function parseEnv(raw: RawEnv): Env {
  const result = EnvSchema.safeParse(raw);

  if (!result.success) {
    const problems = result.error.issues
      .map((issue) => `${issue.path.join(".") || "(root)"}: ${issue.message}`)
      .join("; ");

    throw new ConfigError(
      `Invalid app configuration — ${problems}. Copy .env.example to .env.local and fill it in.`,
    );
  }

  return {
    apiUrl: result.data.EXPO_PUBLIC_API_URL,
    environment: result.data.EXPO_PUBLIC_ENV,
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
    throw new ConfigError("Config read before bootstrap validated it. Call loadEnv() first.");
  }
  return loaded;
}
