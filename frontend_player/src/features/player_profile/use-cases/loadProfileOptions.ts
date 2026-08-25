/**
 * What the profile steps are drawn from, in the app's own words.
 *
 * Read from the server rather than restated here: the tag vocabulary is a closed set the
 * backend owns and the commit re-validates against, and this route exists precisely so that
 * neither client keeps its own copy of it.
 */

import { getProfileOptions } from '../api/playerProfileApi';
import type { ProfileOptions } from '../domain/ProfileOptions';
import { toProfileOptions } from '../mappers/playerProfileMappers';

export interface LoadProfileOptionsInput {
  readonly signal?: AbortSignal;
}

export function loadProfileOptions({
  signal,
}: LoadProfileOptionsInput = {}): Promise<ProfileOptions> {
  return getProfileOptions({ signal }).then(toProfileOptions);
}
