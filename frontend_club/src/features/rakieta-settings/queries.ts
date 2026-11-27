import 'server-only';

import { stepDone, toSetup } from '@/features/overview/mappers';
import { readAsClub } from '@/server/club';

import { toRakietaSettings, type RakietaSettings } from './mappers';

/**
 * **The club's Rakieta settings**: what Groups says of other clubs' courts (the screens B8) reads
 * them too.
 */
export async function getRakietaSettings(): Promise<RakietaSettings> {
  const outcome = await readAsClub((api, auth) => api.GET('/api/v1/club/rakieta-settings', auth));
  if (!outcome.ok) {
    throw new Error(`The club's Rakieta settings could not be read: ${outcome.error.code}`);
  }
  return toRakietaSettings(outcome.data);
}

/**
 * **The club's Rakieta settings, and whether it has confirmed them**: the page's button confirms
 * them the first time and saves them after, as the setup checklist says.
 */
export async function getSettingsPage(): Promise<{
  settings: RakietaSettings;
  confirmed: boolean;
}> {
  const [settings, setup] = await Promise.all([
    getRakietaSettings(),
    readAsClub((api, auth) => api.GET('/api/v1/club/setup', auth)),
  ]);
  if (!setup.ok) throw new Error(`The setup checklist could not be read: ${setup.error.code}`);
  return { settings, confirmed: stepDone(toSetup(setup.data), 'SETTINGS') };
}
