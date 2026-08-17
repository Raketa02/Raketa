/**
 * Public configuration — the values that are deliberately baked into the client bundle.
 *
 * **NOTHING HERE IS SECRET.** Every `NEXT_PUBLIC_*` value is inlined into the JavaScript
 * the browser downloads and can be read out of a shipped page; these are *config*. A
 * secret the browser appears to need is a design error and belongs behind the BFF.
 *
 * The list is short on purpose, and what is *missing* from it is the point (§20.1):
 *
 * - **no FastAPI origin** — the browser must never learn it (ADR-0007, §4.1);
 * - **no environment name** — the badge reads the server-only value through a Server
 *   Component, so there is exactly one copy and nothing to drift out of step;
 * - **no session cookie policy** — the BFF is the only thing that writes the cookie.
 *
 * The server counterpart is `./server`. Two schemas, never one.
 */

import { z } from "zod";

import { httpUrlField, parseOrThrow } from "./environment";

/**
 * The app's own origin is the one thing the browser legitimately needs and cannot always
 * derive — a canonical absolute URL for metadata, share links and redirect construction.
 *
 * Its *scheme* is checked against the environment in `./server`, not here: only the server
 * knows which environment this is, and importing that knowledge to check it would put the
 * environment in the bundle, which is exactly what this file exists to avoid.
 */
const PublicFields = z.object({
  NEXT_PUBLIC_APP_URL: httpUrlField,
});

export interface PublicConfig {
  /** This app's own public origin. Safe in the bundle — it is the origin serving it. */
  readonly appUrl: string;
}

export type RawPublicEnv = Readonly<Partial<Record<keyof z.infer<typeof PublicFields>, string>>>;

const REMEDY = "Copy .env.example to .env.local and fill it in.";

/** Pure: validate a raw environment and map it onto the app's public configuration. */
export function parsePublicConfig(raw: RawPublicEnv): PublicConfig {
  const parsed = parseOrThrow(PublicFields, raw, REMEDY);

  return { appUrl: parsed.NEXT_PUBLIC_APP_URL };
}

/**
 * Spelled out at a statically written member access, because that is the only form Next
 * substitutes at build time. See `./server`'s twin.
 */
function readRawPublicEnv(): RawPublicEnv {
  return { NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL };
}

let loaded: PublicConfig | undefined;

/** The validated public configuration. Memoized; safe on the server and in the browser. */
export function getPublicConfig(): PublicConfig {
  loaded ??= parsePublicConfig(readRawPublicEnv());
  return loaded;
}
