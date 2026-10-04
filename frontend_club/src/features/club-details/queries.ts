import 'server-only';

import { connection } from 'next/server';
import { cache } from 'react';

import { readAsClub } from '@/server/club';
import { loadConfig } from '@/server/config';

import { toClub, type Club, type MapSettings } from './mappers';

/**
 * **The signed-in club's details**, read once per request: the frame's top bar and Club details
 * both ask, and `cache` makes that one call.
 */
export const getClub = cache(async (): Promise<Club> => {
  const outcome = await readAsClub((api, auth) => api.GET('/api/v1/club/details', auth));
  if (!outcome.ok) throw new Error(`The club's details could not be read: ${outcome.error.code}`);
  return toClub(outcome.data);
});

/**
 * **What the map needs, from the server it runs on** — the tile URL and where it opens.
 *
 * `connection()` makes the page that asks render per request. Without it, a page that reads the
 * configuration and nothing else about the request (sign-up) is prerendered at build time, and
 * the build's values are frozen into its HTML: a site built by the e2e suite and started with a
 * real `.env.local` sent every tile to the stub's port and drew a blank map. Configuration is the
 * running server's (docs/environments.md), so the read waits for a request.
 */
export async function mapSettings(): Promise<MapSettings> {
  await connection();
  const config = loadConfig();
  return { tileUrl: config.mapTileUrl, start: config.mapStart };
}
