/**
 * **Fetch this environment's datafile, check it, and keep it** — ADR-0206 §6's first rung.
 *
 * A datafile this build cannot read is **refused**: it fails the fetch rather than arriving, so
 * whichever datafile was in use stays in use (§10) and the device's saved copy is not overwritten
 * with something the next launch could not read either.
 */

import type { AppEnvironment } from '@/shared/config/env';
import { AppError, unknownFailure } from '@/shared/errors';

import { fetchDatafile, type Cancellable } from '../api/datafileApi';
import { saveDatafile } from '../api/datafileCache';
import type { Datafile } from '../domain/featureFlags';
import { readDatafile, type DatafileRefusal } from '../schemas/datafileSchema';

export async function refreshDatafile(
  environment: AppEnvironment,
  options: Cancellable = {},
): Promise<Datafile> {
  const reading = readDatafile(await fetchDatafile(environment, options));

  if (!reading.readable) throw refused(reading.reason);

  await saveDatafile(environment, reading.datafile);
  return reading.datafile;
}

/**
 * A refusal is **terminal**: the same file is served until the flags repo changes it, so asking
 * again returns the same answer. The next foreground asks anyway, which is when it might differ.
 */
function refused(reason: DatafileRefusal): AppError {
  return unknownFailure(
    reason === 'unknown-schema-version'
      ? 'The feature datafile is in a format this build does not read.'
      : 'The feature datafile could not be read.',
  );
}
