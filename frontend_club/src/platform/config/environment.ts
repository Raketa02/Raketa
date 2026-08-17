/**
 * The environment vocabulary, shared by both configuration schemas.
 *
 * Pure: no `process.env`, no `server-only`, no I/O. Both the server schema and the public
 * schema build on this, and the environment badge reads the label table — so the four
 * names, the scheme rule and the badge exist exactly once.
 *
 * This module does **not** hold configuration; it holds the vocabulary configuration is
 * validated against. Nothing here is a value read from the process, which is why it is
 * safe for a Client Component to reach — it carries no environment, only the shape one
 * must have.
 *
 * See docs/architecture/production-architecture.md §20.1.
 */

import { z } from "zod";

/**
 * The four environments, named identically by all three apps.
 *
 * `local` is a developer's own machine and is the only one that runs today.
 * `development` and `staging` are defined and validated but **not provisioned** — no
 * domain is registered — and `production` does not exist yet either. Selecting one is a
 * startup failure rather than a silent fallback to whatever happens to be reachable.
 *
 * Not to be confused with `NODE_ENV`, which has two values and describes how the app was
 * *compiled*. A build mode is not an environment: one production build runs in staging
 * and in production alike, and reading it to answer an environment question is the bug
 * this enum exists to remove. Nothing in this app reads it — a lint rule says so.
 */
export const ENVIRONMENTS = ["local", "development", "staging", "production"] as const;

export type AppEnvironment = (typeof ENVIRONMENTS)[number];

/** Spelled once, for the refusal message and for the environment template. */
const ENVIRONMENT_NAMES = ENVIRONMENTS.join(", ");

/**
 * The scheme a **public-network** URL must use, per environment — `null` where either is
 * legitimate. Part of the contract, not a convention.
 *
 * "Public-network" is load-bearing, and it is the distinction #99 settled across the three
 * apps. This table governs a URL a *browser or a phone* reaches over the internet, where
 * `http://` in a deployed environment means a session cookie in the clear. It does **not**
 * govern a URL one server tier uses to reach another: `http://backend.svc.cluster.local:8000`
 * never leaves the cluster, is entirely legitimate, and the rule as first written in #96
 * refused it. So `BACKEND_API_URL` is validated for shape and no further, and this table is
 * applied only to `NEXT_PUBLIC_APP_URL` — the origin a browser actually visits.
 *
 * `local` is `null` for the same reason the player app's is: a laptop can legitimately be
 * reached over either, a tunnel hands back `https://`, and nothing about `local` is
 * protected by forbidding TLS on it.
 *
 * Written out per environment rather than as `environment === "local" ? … : …` so that a
 * fifth environment fails to compile until somebody decides how it is reached.
 */
export const REQUIRED_SCHEME: Readonly<Record<AppEnvironment, "https://" | null>> = {
  local: null,
  development: "https://",
  staging: "https://",
  production: "https://",
};

/**
 * What the environment badge says, or `null` where it says nothing.
 *
 * The same four labels the player app uses, so a screenshot from either app reads the
 * same way. Written out per environment for the same reason `REQUIRED_SCHEME` is: a fifth
 * environment must fail to compile until somebody decides what it is called, rather than
 * silently inheriting production's unbadged look — the one wrong answer that is invisible.
 *
 * `string | null`, not a boolean beside a label: two fields can disagree, and *badged with
 * nothing written on it* is a state readers would have to defend against.
 */
export const ENVIRONMENT_BADGE: Readonly<Record<AppEnvironment, string | null>> = {
  local: "LOCAL",
  development: "DEVELOPMENT",
  staging: "STAGING",
  production: null,
};

/**
 * Startup configuration is unusable rather than merely wrong, so it gets its own error
 * type: it is raised before the session, the FastAPI client and the normalized error
 * envelope exist, and no error category applies to it.
 */
export class ConfigError extends Error {
  override readonly name = "ConfigError";
}

/**
 * The environment field, shared by every schema that needs one.
 *
 * The message is replaced rather than left to zod, whose `invalid_enum_value` text ends
 * `received '…'`. Config lands in logs and crash reports, and a variable's value is never
 * something a refusal echoes back — the same rule the URLs follow.
 */
export const environmentField = z.enum(ENVIRONMENTS, {
  errorMap: () => ({ message: `must be one of ${ENVIRONMENT_NAMES}` }),
});

/**
 * An absolute HTTP(S) URL.
 *
 * `.url()` alone is not enough: WHATWG parsing accepts `localhost:8000` as a URL whose
 * *protocol* is `localhost:`, and that is precisely what someone types. It would pass
 * validation and then fail on every request.
 */
export const httpUrlField = z
  .string()
  .url()
  .refine((value) => /^https?:\/\//i.test(value), {
    message: "must start with http:// or https://",
  });

/**
 * The scheme rule is a claim about a URL and the environment *together*, so it is checked
 * on the object rather than on either field. Apply it only to a URL that crosses a public
 * network — see `REQUIRED_SCHEME`.
 *
 * **It stays silent when the field itself already refused the value**, and that guard is
 * measured rather than assumed. A failing `.url()` or `.refine()` leaves zod's result
 * *dirty* rather than aborting it, so an object-level refinement still runs over the
 * rejected string — and `localhost:8000` was reported both as a malformed URL and as a
 * scheme mismatch, two complaints for one typo, the second of them pointing at the
 * environment rather than at the missing scheme. Re-running the field is what makes
 * "a malformed URL is reported as a malformed URL" true instead of merely intended.
 *
 * The issue is attached to the URL — that is the value that has to change — and names the
 * environment as the reason. An environment name is not a secret and is already on every
 * log record; it is the *reason* here, never the offending value.
 */
export function requireScheme(
  ctx: z.RefinementCtx,
  environment: AppEnvironment,
  field: string,
  value: string,
): void {
  if (!httpUrlField.safeParse(value).success) return;

  const scheme = REQUIRED_SCHEME[environment];

  if (scheme === null) return;

  if (!value.toLowerCase().startsWith(scheme)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: [field],
      message: `must start with ${scheme} when APP_ENV is ${environment}`,
    });
  }
}

/**
 * Parse a raw environment, or throw `ConfigError` naming the offending variables and why
 * — **never their values**, because config lands in logs and crash reports and a URL can
 * carry credentials.
 *
 * One implementation, so both schemas refuse in the same shape and neither can drift into
 * echoing a value.
 */
export function parseOrThrow<Schema extends z.ZodTypeAny>(
  schema: Schema,
  raw: unknown,
  remedy: string,
): z.infer<Schema> {
  const result = schema.safeParse(raw);

  if (!result.success) {
    const problems = result.error.issues
      .map((issue) => `${issue.path.join(".") || "(root)"}: ${issue.message}`)
      .join("; ");

    throw new ConfigError(`Invalid club app configuration — ${problems}. ${remedy}`);
  }

  return result.data;
}
