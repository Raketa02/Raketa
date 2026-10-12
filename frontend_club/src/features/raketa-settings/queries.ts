import 'server-only';

import { stepDone, toSetup } from '@/features/overview/mappers';
import { readAsClub } from '@/server/club';

import { toWayAndSettings, type WayAndSettings } from './mappers';

/**
 * **How the club works with Raketa, and its settings**: what Groups says of other clubs' courts
 * (the screens B8) reads them too.
 */
export async function getWayAndSettings(): Promise<WayAndSettings> {
  const outcome = await readAsClub((api, auth) => api.GET('/api/v1/club/raketa-settings', auth));
  if (!outcome.ok) {
    throw new Error(`The club's Raketa settings could not be read: ${outcome.error.code}`);
  }
  return toWayAndSettings(outcome.data);
}

/**
 * **How the club works with Raketa, and whether it has confirmed its settings**: the page's
 * button confirms them the first time and saves them after, as the setup checklist says.
 */
export async function getRaketaSettings(): Promise<{
  settings: WayAndSettings;
  confirmed: boolean;
}> {
  const [settings, setup] = await Promise.all([
    getWayAndSettings(),
    readAsClub((api, auth) => api.GET('/api/v1/club/setup', auth)),
  ]);
  if (!setup.ok) throw new Error(`The setup checklist could not be read: ${setup.error.code}`);
  return { settings, confirmed: stepDone(toSetup(setup.data), 'SETTINGS') };
}
