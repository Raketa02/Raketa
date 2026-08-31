/**
 * Read the three profile facts the Play screens hold.
 *
 * A pass-through over one request and one mapper, which is the uniform-strict shape
 * `docs/architecture.md` Part 1 sanctions: there is no rule to apply on the way in, and the
 * decisions this read *does* make — a cleared week is an answer, an absent sport is
 * undeclared, an unreadable code is dropped — are the mapper's and are stated there.
 */

import { readPlayerProfile } from '../api/playerProfileApi';
import type { PlayerProfileSurface } from '../domain/PlayerProfileSurface';
import { toPlayerProfileSurface } from '../mappers/playerProfileMappers';

export interface ReadProfileSurfaceOptions {
  readonly signal?: AbortSignal;
}

export function readProfileSurface({
  signal,
}: ReadProfileSurfaceOptions = {}): Promise<PlayerProfileSurface> {
  return readPlayerProfile({ signal }).then(toPlayerProfileSurface);
}
