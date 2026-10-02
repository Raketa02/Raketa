import 'server-only';

import { stepDone, toSetup } from '@/features/overview/mappers';
import { readAsClub } from '@/server/club';

import { toWayAndSettings, type WayAndSettings } from './mappers';

/**
 * **How the club works with Raketa, and whether it has confirmed its settings**: the page's
 * button confirms them the first time and saves them after, as the setup checklist says.
 */
export async function getRaketaSettings(): Promise<{
  settings: WayAndSettings;
  confirmed: boolean;
}> {
  const [settings, setup] = await Promise.all([
    readAsClub((api, auth) => api.GET('/api/v1/club/raketa-settings', auth)),
    readAsClub((api, auth) => api.GET('/api/v1/club/setup', auth)),
  ]);
  if (!settings.ok) {
    throw new Error(`The club's Raketa settings could not be read: ${settings.error.code}`);
  }
  if (!setup.ok) throw new Error(`The setup checklist could not be read: ${setup.error.code}`);
  return {
    settings: toWayAndSettings(settings.data),
    confirmed: stepDone(toSetup(setup.data), 'SETTINGS'),
  };
}
