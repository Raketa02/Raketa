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
 * address, the two stores and the app's scheme; and so is every identifier the app-link files name:
 * the Apple team and bundle, and the Android package and its signing keys. Server-side only: nothing here is a
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
 * An absolute http(s) URL that parses. `z.url()` alone accepts `localhost:8000`, whose *protocol*
 * is `localhost:` — exactly what someone types.
 */
const httpUrl = z
  .string({ error: required('must be an absolute http:// or https:// URL') })
  // One check, so one complaint: `https://[play.google.com` starts like a URL and parses as none,
  // and the Android store button's address is built from its setting by parsing it.
  .refine((url) => /^https?:\/\/[^\s/]+/i.test(url) && URL.canParse(url), {
    error: 'must be an absolute http:// or https:// URL',
  });

/** A SHA-256 certificate fingerprint as Android prints one: 32 hex pairs joined by colons. */
const FINGERPRINT = /^([0-9A-F]{2}:){31}[0-9A-F]{2}$/i;

function fingerprintsOf(value: string): string[] {
  return value.split(',').map((part) => part.trim().toUpperCase());
}

/** A string `pattern` matches, refused with one sentence whether it is missing or malformed. */
function matching(pattern: RegExp, otherwise: string) {
  return z.string({ error: required(otherwise) }).regex(pattern, { error: otherwise });
}

/** An identifier in dots, such as `com.raketa.player`: `part` is what one piece may be. */
function dotted(part: string, otherwise: string) {
  return matching(new RegExp(`^${part}(\\.${part})+$`), otherwise);
}

const FINGERPRINTS = 'must be SHA-256 fingerprints (32 hex pairs, AA:BB:…), separated by commas';

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
   * `<APP_SCHEME>://<route>`, such as `join/<code>`. The app declares one scheme at every
   * environment (`frontend_player`'s `app.config.ts`), and so does the backend's `APP_SCHEME`.
   */
  APP_SCHEME: matching(
    /^[a-z][a-z0-9+.-]*$/i,
    'must be a URL scheme such as raketa, without ://',
  ).refine((scheme) => !NOT_AN_APP_SCHEME.includes(scheme.toLowerCase()), {
    error: "must be the app's own scheme, not a web or script scheme",
  }),
  /** The Apple developer team the app is signed by: Apple's association file names it. */
  APPLE_TEAM_ID: matching(
    /^[A-Z0-9]{10}$/,
    'must be the 10-character Apple team id, capitals and digits',
  ),
  /** The iOS app's bundle id (`frontend_player`'s `ios.bundleIdentifier`). */
  IOS_BUNDLE_ID: dotted('[A-Za-z0-9-]+', 'must be a bundle id such as com.raketa.player'),
  /** The Android app's package (`frontend_player`'s `android.package`). */
  ANDROID_PACKAGE: dotted(
    '[A-Za-z][A-Za-z0-9_]*',
    'must be an Android package name such as com.raketa.player',
  ),
  /**
   * The SHA-256 fingerprints of every key the Android app is signed with, separated by commas: a
   * release key, and a store's re-signing key once there is one.
   */
  ANDROID_CERT_FINGERPRINTS: z
    .string({ error: required(FINGERPRINTS) })
    .refine((value) => fingerprintsOf(value).every((key) => FINGERPRINT.test(key)), {
      error: FINGERPRINTS,
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
  readonly appleTeamId: string;
  readonly iosBundleId: string;
  readonly androidPackage: string;
  /** Upper case, as Android compares them. */
  readonly androidCertFingerprints: readonly string[];
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
    appleTeamId: data.APPLE_TEAM_ID,
    iosBundleId: data.IOS_BUNDLE_ID,
    androidPackage: data.ANDROID_PACKAGE,
    androidCertFingerprints: fingerprintsOf(data.ANDROID_CERT_FINGERPRINTS),
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
    APPLE_TEAM_ID: process.env.APPLE_TEAM_ID,
    IOS_BUNDLE_ID: process.env.IOS_BUNDLE_ID,
    ANDROID_PACKAGE: process.env.ANDROID_PACKAGE,
    ANDROID_CERT_FINGERPRINTS: process.env.ANDROID_CERT_FINGERPRINTS,
  });
  return loaded;
}
