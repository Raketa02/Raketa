import 'server-only';

import { z } from 'zod';

import { loadConfig, type Point } from './config';

/**
 * **The address search**: one place for a typed address, from the geocoder at `GEOCODER_URL` —
 * Nominatim's `/search`, or anything answering its `jsonv2` shape. The desk types an address over
 * the map, and the best match becomes the pin.
 *
 * **Called from this server, never from the browser**, for Nominatim's usage policy: a caller
 * says who it is (`User-Agent`, which a browser may not set), and asks at most once a second. This
 * process keeps the second itself: searches queue, one at a time, a second apart. The endpoint is
 * reached by a server action anybody can call, sign-up being signed out, so the queue is also what
 * keeps a burst of calls from becoming a burst at the geocoder.
 *
 * **Near the map, not inside it**: the search prefers places around where the map opens
 * (`MAP_START`) without being bounded to them, so a club in another city is still found.
 *
 * It answers with an outcome, as the backend's doors do (`docs/architecture.md` §4), and logs a
 * failure by kind and status, never with the address.
 */

/** No search waits longer than this for an answer; past it, the geocoder counts as unreachable. */
const TIMEOUT_MS = 10_000;

/** Nominatim's usage policy: at most one request a second from one application. */
const SPACING_MS = 1_000;

/** How far either side of the map's opening point the search prefers answers, in degrees. */
const NEAR = 0.5;

/** The `jsonv2` answer, best first; everything but the three fields read here is ignored. */
const Answer = z.array(z.object({ lat: z.string(), lon: z.string(), display_name: z.string() }));

export interface FoundPlace {
  readonly point: Point;
  /** The geocoder's own name for what it found, said back so the desk can check it. */
  readonly name: string;
}

export type PlaceOutcome =
  | { readonly ok: true; readonly place: FoundPlace }
  | { readonly ok: false; readonly code: 'place_not_found' | 'geocoder_unreachable' };

const UNREACHABLE: PlaceOutcome = { ok: false, code: 'geocoder_unreachable' };

let queue: Promise<void> = Promise.resolve();
let lastAt = 0;

/** This process's turn at the geocoder: one search at a time, a second after the last. */
function turn(): Promise<void> {
  const mine = queue.then(async () => {
    const wait = lastAt + SPACING_MS - Date.now();
    if (wait > 0) await new Promise((resolve) => setTimeout(resolve, wait));
    lastAt = Date.now();
  });
  queue = mine;
  return mine;
}

/** The best match for `query`, which the caller has already trimmed and bounded. */
export async function geocode(query: string): Promise<PlaceOutcome> {
  const config = loadConfig();
  const { latitude, longitude } = config.mapStart;
  const url = new URL(config.geocoderUrl);
  url.searchParams.set('q', query);
  url.searchParams.set('format', 'jsonv2');
  url.searchParams.set('limit', '1');
  // west, north, east, south: Nominatim's `viewbox` is two corners as longitude,latitude pairs.
  url.searchParams.set(
    'viewbox',
    [longitude - NEAR, latitude + NEAR, longitude + NEAR, latitude - NEAR].join(','),
  );
  url.searchParams.set('bounded', '0');

  await turn();
  let response: Response;
  try {
    response = await fetch(url, {
      headers: {
        'User-Agent': `Raketa for Clubs (${config.environment})`,
        Accept: 'application/json',
      },
      cache: 'no-store',
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch {
    console.error('[club] geocoder unreachable');
    return UNREACHABLE;
  }
  if (!response.ok) {
    console.error(`[club] geocoder refused: ${response.status}`);
    return UNREACHABLE;
  }

  const answer = Answer.safeParse(await response.json().catch(() => null));
  if (!answer.success) {
    console.error('[club] geocoder answered in an unknown shape');
    return UNREACHABLE;
  }
  const best = answer.data[0];
  if (best === undefined) return { ok: false, code: 'place_not_found' };
  const point = { latitude: Number(best.lat), longitude: Number(best.lon) };
  if (!Number.isFinite(point.latitude) || !Number.isFinite(point.longitude)) return UNREACHABLE;
  return { ok: true, place: { point, name: best.display_name } };
}
