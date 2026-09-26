/**
 * **The public site's configuration**: read once, validated once, when the server starts.
 *
 * Every variable is required and none has a default ([`docs/environments.md`](../../../docs/environments.md)):
 * absence is itself the refusal, and the message names the variable. `src/instrumentation.ts`
 * calls {@link loadConfig} before the server takes a request, so a missing value stops
 * `next start` rather than surfacing as a page with a dead button.
 *
 * **A refusal names the variable and the reason, and never the value.** A URL can carry
 * credentials, and a refusal lands in a log.
 *
 * **Every address is a setting, never a literal** (ADR-0187 §7): the backend, this site's own
 * address, the two stores and the app's scheme. Server-side only: nothing here is a
 * `NEXT_PUBLIC_*` variable, so nothing is inlined into the browser's bundle. A page receives the
 * addresses it links to as props.
 */

import 'server-only';

import { z } from 'zod';

/**
 * The four environments, named identically by every app. **Only `local` runs today**;
 * `development` and `staging` are defined and validated but not provisioned, and `production`
 * does not exist yet (ADR-0028).
 */
export const ENVIRONMENTS = ['local', 'development', 'staging', 'production'] as const;

export type AppEnvironment = (typeof ENVIRONMENTS)[number];

/**
 * The scheme a URL the **browser** or a messenger reaches must use, per environment: `null`
 * where either is legitimate. Written out per environment so that a fifth fails to compile until
 * somebody decides how it is reached.
 */
const BROWSER_SCHEME: Readonly<Record<AppEnvironment, 'https://' | null>> = {
  local: null,
  development: 'https://',
  staging: 'https://',
  production: 'https://',
};

/** The variables a browser or a messenger opens, which the scheme rule holds to https. */
const BROWSER_URLS = ['PUBLIC_SITE_URL', 'APP_STORE_URL', 'GOOGLE_PLAY_URL'] as const;

/**
 * Schemes that are never an app's: a link built from one would open a web page, run script, or
 * read a file instead of opening Raketa.
 */
const NOT_AN_APP_SCHEME = ['http', 'https', 'javascript', 'data', 'vbscript', 'file', 'blob'];

/** Absent and present-but-wrong are two sentences, and neither repeats the input. */
function required(otherwise: string) {
  return (issue: { input?: unknown }) => (issue.input === undefined ? 'is required' : otherwise);
}

/**
 * An absolute http(s) URL. `z.url()` alone accepts `localhost:8000`, whose *protocol* is
 * `localhost:` — exactly what someone types.
 */
const httpUrl = z
  .string({ error: required('must be an absolute http:// or https:// URL') })
  .regex(/^https?:\/\/[^\s/]+/i, { error: 'must be an absolute http:// or https:// URL' });

const Fields = z.object({
  APP_ENV: z.enum(ENVIRONMENTS, { error: required(`must be one of ${ENVIRONMENTS.join(', ')}`) }),
  /**
   * The backend's base URL, called from this server and never from the browser. Server to
   * server, so no scheme rule (docs/environments.md, *The scheme rule*).
   */
  API_URL: httpUrl,
  /**
   * **This site's own address**, the one the backend prints every group link under (its own
   * `PUBLIC_SITE_URL`). A messenger reads the preview's image and address as absolute URLs made
   * from it, so it is the address people reach, not the one this process listens on.
   */
  PUBLIC_SITE_URL: httpUrl,
  /** Where the App Store button goes: Raketa's listing. */
  APP_STORE_URL: httpUrl,
  /** Where the Google Play button goes: Raketa's listing. */
  GOOGLE_PLAY_URL: httpUrl,
  /**
   * The player app's own scheme, without `://`: **Open in Raketa** goes to
   * `<APP_SCHEME>://join/<code>`. The app declares one scheme at every environment
   * (`frontend_player`'s `app.config.ts`), and so does the backend's `APP_SCHEME`.
   */
  APP_SCHEME: z
    .string({ error: required('must be a URL scheme such as raketa, without ://') })
    .regex(/^[a-z][a-z0-9+.-]*$/i, { error: 'must be a URL scheme such as raketa, without ://' })
    .refine((scheme) => !NOT_AN_APP_SCHEME.includes(scheme.toLowerCase()), {
      error: "must be the app's own scheme, not a web or script scheme",
    }),
});

/**
 * **The scheme rule, checked beside the fields rather than as a zod refinement.** A refinement on
 * the object is skipped once any field has failed, and then a missing variable would hide a store
 * link served in the clear. Silent when the field itself already refused the value: one typo, one
 * complaint.
 */
function schemeProblems(raw: RawConfig): string[] {
  const environment = ENVIRONMENTS.find((name) => name === raw.APP_ENV);
  if (environment === undefined) return [];
  const scheme = BROWSER_SCHEME[environment];
  if (scheme === null) return [];
  return BROWSER_URLS.flatMap((name) => {
    const url = raw[name];
    if (url === undefined || !httpUrl.safeParse(url).success) return [];
    return url.toLowerCase().startsWith(scheme)
      ? []
      : [`${name}: must start with ${scheme} when APP_ENV is ${environment}`];
  });
}

export type RawConfig = Readonly<Partial<Record<keyof z.infer<typeof Fields>, string>>>;

export interface Config {
  readonly environment: AppEnvironment;
  readonly apiUrl: string;
  readonly siteUrl: string;
  readonly appStoreUrl: string;
  readonly googlePlayUrl: string;
  readonly appScheme: string;
}

export class ConfigError extends Error {
  override readonly name = 'ConfigError';
}

/**
 * A variable set to nothing is a variable not set: `APP_SCHEME=` is a template line nobody
 * filled in, and is told *is required* like one that is missing.
 */
function withoutBlanks(raw: RawConfig): RawConfig {
  return Object.fromEntries(
    Object.entries(raw).filter(([, value]) => value !== undefined && value.trim() !== ''),
  );
}

/** Pure: validate a raw environment, or throw naming every offending variable and why. */
export function parseConfig(raw: RawConfig): Config {
  const present = withoutBlanks(raw);
  const result = Fields.safeParse(present);
  const problems = [
    ...(result.success
      ? []
      : result.error.issues.map(
          (issue) => `${issue.path.join('.') || '(root)'}: ${issue.message}`,
        )),
    ...schemeProblems(present),
  ];
  if (!result.success || problems.length > 0) {
    throw new ConfigError(
      `Invalid public site configuration — ${problems.join('; ')}. Copy .env.example to .env.local and fill it in.`,
    );
  }
  const data = result.data;
  return {
    environment: data.APP_ENV,
    apiUrl: data.API_URL.replace(/\/+$/, ''),
    siteUrl: data.PUBLIC_SITE_URL.replace(/\/+$/, ''),
    appStoreUrl: data.APP_STORE_URL,
    googlePlayUrl: data.GOOGLE_PLAY_URL,
    appScheme: data.APP_SCHEME.toLowerCase(),
  };
}

let loaded: Config | undefined;

/** Validate and memoize. The one function here that reads `process.env`. */
export function loadConfig(): Config {
  loaded ??= parseConfig({
    APP_ENV: process.env.APP_ENV,
    API_URL: process.env.API_URL,
    PUBLIC_SITE_URL: process.env.PUBLIC_SITE_URL,
    APP_STORE_URL: process.env.APP_STORE_URL,
    GOOGLE_PLAY_URL: process.env.GOOGLE_PLAY_URL,
    APP_SCHEME: process.env.APP_SCHEME,
  });
  return loaded;
}
