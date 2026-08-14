/**
 * The sports the platform serves, for the picker.
 *
 * Read from the server rather than restated here: the registry is closed and lives in the
 * backend's shared kernel, and the route exists so that neither client hardcodes it.
 */

import { listSports as fetchSports } from '../api/onboardingApi';
import type { Sport } from '../domain/Sport';
import { toSports } from '../mappers/onboardingMappers';

export interface ListSportsOptions {
  readonly signal?: AbortSignal;
}

export function listSports({ signal }: ListSportsOptions = {}): Promise<readonly Sport[]> {
  return fetchSports({ signal }).then(toSports);
}
