import 'server-only';

import { readAsClub } from '@/server/club';

import { toAdministrator, type Administrator } from './mappers';

/** **The club's administrators**, by name, with where each one stands as of now. */
export async function getAdministrators(): Promise<readonly Administrator[]> {
  const outcome = await readAsClub((api, auth) => api.GET('/api/v1/club/administrators', auth));
  if (!outcome.ok) {
    throw new Error(`The club's administrators could not be read: ${outcome.error.code}`);
  }
  const now = Date.now();
  return outcome.data.administrators.map((wire) => toAdministrator(wire, now));
}
