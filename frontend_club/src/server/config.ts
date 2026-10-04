/**
 * **The club website's configuration**: read once, validated once, when the server starts.
 *
 * Every variable is required and none has a default ([`docs/environments.md`](../../../docs/environments.md)):
 * absence is itself the refusal, and the message names the variable. `src/instrumentation.ts`
 * calls {@link loadConfig} before the server takes a request, so a missing value stops
 * `next start` rather than surfacing three pages deep as a failed call.
 *
 * **A refusal names the variable and the reason, and never the value.** A URL can carry
 * credentials, the session secret is a secret, and a refusal lands in a log.
 *
 * Server-side only: nothing here is a `NEXT_PUBLIC_*` variable, so nothing is inlined into the
 * browser's bundle. The one value the browser needs, the tile URL, reaches it as a prop the
 * server hands the map; the address search's URL never leaves the server.
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
 * The scheme a URL the **browser** reaches must use, per environment: `null` where either is
 * legitimate. Written out per environment so that a fifth fails to compile until somebody
 * decides how it is reached.
 */
const BROWSER_SCHEME: Readonly<Record<AppEnvironment, 'https://' | null>> = {
  local: null,
  development: 'https://',
  staging: 'https://',
  production: 'https://',
};

/**
 * The session secret's floor. iron-session refuses a password under 32 characters at the first
 * seal, which would be a refused sign-in rather than a refused start.
 */
const SESSION_SECRET_MIN = 32;

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
  /** Seals the session cookie. `openssl rand -hex 32`. */
  SESSION_SECRET: z
    .string({ error: required(`must be at least ${SESSION_SECRET_MIN} characters`) })
    .min(SESSION_SECRET_MIN, { error: `must be at least ${SESSION_SECRET_MIN} characters` }),
  /**
   * The map's tile template. The browser fetches it, over the public network, so it is
   * `https://` when deployed. OpenStreetMap's own servers are for development only; a
   * provider that allows production traffic is a deploy-time item (ADR-0187 §3).
   */
  MAP_TILE_URL: httpUrl.refine((url) => ['{z}', '{x}', '{y}'].every((part) => url.includes(part)), {
    error: 'must contain {z}, {x} and {y}',
  }),
  /**
   * The address search's endpoint: Nominatim's `/search`, or anything answering its `jsonv2`
   * shape. Called from this server and never from the browser, so it carries no scheme rule,
   * as `API_URL` does not. Nominatim's own server is for light use under its usage policy; a
   * provider for production traffic is a deploy-time item, as the tiles' is (ADR-0187 §3).
   */
  GEOCODER_URL: httpUrl,
  /** Where the map opens before a pin is dropped: `latitude,longitude` in decimal degrees. */
  MAP_START: z
    .string({ error: required('must be "latitude,longitude" in decimal degrees') })
    .refine((value) => parsePoint(value) !== null, {
      error: 'must be "latitude,longitude" in decimal degrees',
    }),
});

/**
 * **The scheme rule, checked beside the fields rather than as a zod refinement.** A refinement on
 * the object is skipped once any field has failed, and then a missing secret would hide a tile
 * URL served in the clear. Silent when the field itself already refused the value: one typo, one
 * complaint.
 */
function schemeProblems(raw: RawConfig): string[] {
  const environment = ENVIRONMENTS.find((name) => name === raw.APP_ENV);
  if (environment === undefined) return [];
  const scheme = BROWSER_SCHEME[environment];
  const url = raw.MAP_TILE_URL;
  if (scheme === null || url === undefined || !httpUrl.safeParse(url).success) return [];
  return url.toLowerCase().startsWith(scheme)
    ? []
    : [`MAP_TILE_URL: must start with ${scheme} when APP_ENV is ${environment}`];
}

export type RawConfig = Readonly<Partial<Record<keyof z.infer<typeof Fields>, string>>>;

export interface Point {
  readonly latitude: number;
  readonly longitude: number;
}

export interface Config {
  readonly environment: AppEnvironment;
  readonly apiUrl: string;
  readonly sessionSecret: string;
  readonly mapTileUrl: string;
  readonly mapStart: Point;
  readonly geocoderUrl: string;
}

export class ConfigError extends Error {
  override readonly name = 'ConfigError';
}

function parsePoint(value: string): Point | null {
  const parts = value.split(',').map((part) => part.trim());
  if (parts.length !== 2) return null;
  const [latitude, longitude] = parts.map(Number) as [number, number];
  if (!Number.isFinite(latitude) || Math.abs(latitude) > 90) return null;
  if (!Number.isFinite(longitude) || Math.abs(longitude) > 180) return null;
  if (parts.some((part) => part === '')) return null;
  return { latitude, longitude };
}

/**
 * A variable set to nothing is a variable not set: `SESSION_SECRET=` is a template line nobody
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
      `Invalid club website configuration — ${problems.join('; ')}. Copy .env.example to .env.local and fill it in.`,
    );
  }
  const data = result.data;
  return {
    environment: data.APP_ENV,
    apiUrl: data.API_URL.replace(/\/+$/, ''),
    sessionSecret: data.SESSION_SECRET,
    mapTileUrl: data.MAP_TILE_URL,
    mapStart: parsePoint(data.MAP_START)!,
    geocoderUrl: data.GEOCODER_URL,
  };
}

let loaded: Config | undefined;

/** Validate and memoize. The one function here that reads `process.env`. */
export function loadConfig(): Config {
  loaded ??= parseConfig({
    APP_ENV: process.env.APP_ENV,
    API_URL: process.env.API_URL,
    SESSION_SECRET: process.env.SESSION_SECRET,
    MAP_TILE_URL: process.env.MAP_TILE_URL,
    MAP_START: process.env.MAP_START,
    GEOCODER_URL: process.env.GEOCODER_URL,
  });
  return loaded;
}
