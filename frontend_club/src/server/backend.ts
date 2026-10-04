import 'server-only';

import createClient, { type Client } from 'openapi-fetch';

import type { paths } from '@/generated/schema';

import { loadConfig } from './config';

/**
 * **The typed client over the club surface** (`backend/openapi.club.json`), and the only thing
 * in this app that opens a connection to the backend. Its paths, bodies and answers are the
 * generated contract's; nothing here restates a wire shape.
 */
export type ClubApi = Client<paths>;

/** No call waits longer than this for an answer; past it, the backend counts as unreachable. */
const TIMEOUT_MS = 10_000;

let client: ClubApi | undefined;

export function clubApi(): ClubApi {
  client ??= createClient<paths>({
    baseUrl: loadConfig().apiUrl,
    fetch: (request) => fetch(new Request(request, { signal: AbortSignal.timeout(TIMEOUT_MS) })),
  });
  return client;
}

/** The per-call options that present an access token. */
export function bearer(accessToken: string): { headers: { Authorization: string } } {
  return { headers: { Authorization: `Bearer ${accessToken}` } };
}
