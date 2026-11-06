import 'server-only';

import createClient, { type Client } from 'openapi-fetch';

import type { paths } from '@/generated/schema';

import { loadConfig } from './config';
import { settle, type FetchResult, type Outcome } from './outcome';

/**
 * **The typed client over the public surface** (`backend/openapi.public.json`), and the only
 * thing in this app that opens a connection to the backend. Its paths, bodies and answers are the
 * generated contract's; nothing here restates a wire shape.
 *
 * **There is one door, because there is nobody to be.** The public surface takes no session
 * (ADR-0187 §4), so every call is anonymous and this site holds no token, no cookie and no
 * secret to present.
 */
export type PublicApi = Client<paths>;

/**
 * No call waits longer than this for an answer; past it, the backend counts as unreachable. A
 * photograph it signed a link to waits as long (`photos.ts`).
 */
export const TIMEOUT_MS = 10_000;

let client: PublicApi | undefined;

function publicApi(): PublicApi {
  client ??= createClient<paths>({
    baseUrl: loadConfig().apiUrl,
    fetch: (request) => fetch(new Request(request, { signal: AbortSignal.timeout(TIMEOUT_MS) })),
  });
  return client;
}

/** Call the public surface and settle the answer into an {@link Outcome}. */
export function fromBackend<T>(
  call: (api: PublicApi) => Promise<FetchResult<T>>,
): Promise<Outcome<T>> {
  return settle(() => call(publicApi()));
}
