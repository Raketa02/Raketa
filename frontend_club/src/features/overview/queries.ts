import 'server-only';

import { readAsClub } from '@/server/club';
import { readToldLive } from '@/server/marks';

import { toSetup, type Setup } from './mappers';

/** **The setup checklist**, read off everything the club has set, and whether it is live. */
export async function getSetup(): Promise<Setup> {
  const outcome = await readAsClub((api, auth) => api.GET('/api/v1/club/setup', auth));
  if (!outcome.ok) throw new Error(`The setup checklist could not be read: ${outcome.error.code}`);
  return toSetup(outcome.data);
}

/** Whether this browser has been told the club is live already. */
export async function wasToldLive(): Promise<boolean> {
  return readToldLive();
}
