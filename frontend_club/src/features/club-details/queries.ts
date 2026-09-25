import 'server-only';

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

export function mapSettings(): MapSettings {
  const config = loadConfig();
  return { tileUrl: config.mapTileUrl, start: config.mapStart };
}
