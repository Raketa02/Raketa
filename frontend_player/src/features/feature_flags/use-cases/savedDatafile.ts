/**
 * **The datafile this device saved last** — ADR-0206 §6's second rung, read back at launch.
 *
 * Checked on the way out exactly as a fetched one is on the way in: what is on the device may
 * have been saved by an older build, and a format this one does not read is no cache at all.
 * `null` rather than `undefined` for *looked, and there is none*, so a query can hold the answer.
 */

import type { AppEnvironment } from '@/shared/config/env';

import { readSavedDatafile } from '../api/datafileCache';
import type { Datafile } from '../domain/featureFlags';
import { readDatafile } from '../schemas/datafileSchema';

export async function savedDatafile(environment: AppEnvironment): Promise<Datafile | null> {
  const reading = readDatafile(await readSavedDatafile(environment));
  return reading.readable ? reading.datafile : null;
}
