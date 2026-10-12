import 'server-only';

import { stepDone, toSetup } from '@/features/overview/mappers';
import { readAsClub } from '@/server/club';

import { toRaketaSettings, type RaketaSettings } from './mappers';

/**
 * **The club's Raketa settings**: what Groups says of other clubs' courts (the screens B8) reads
 * them too.
 */
export async function getRaketaSettings(): Promise<RaketaSettings> {
  const outcome = await readAsClub((api, auth) => api.GET('/api/v1/club/raketa-settings', auth));
  if (!outcome.ok) {
    throw new Error(`The club's Raketa settings could not be read: ${outcome.error.code}`);
  }
  return toRaketaSettings(outcome.data);
}

/**
 * **The club's Raketa settings, and whether it has confirmed them**: the page's button confirms
 * them the first time and saves them after, as the setup checklist says.
 */
export async function getSettingsPage(): Promise<{
  settings: RaketaSettings;
  confirmed: boolean;
}> {
  const [settings, setup] = await Promise.all([
    getRaketaSettings(),
    readAsClub((api, auth) => api.GET('/api/v1/club/setup', auth)),
  ]);
  if (!setup.ok) throw new Error(`The setup checklist could not be read: ${setup.error.code}`);
  return { settings, confirmed: stepDone(toSetup(setup.data), 'SETTINGS') };
}
