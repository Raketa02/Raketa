/**
 * Move the player's Location area — to the phone's cell, or to a club she picked.
 *
 * **The only way a location moves after onboarding**, and a reading arrives as the **area**,
 * never the fix: `areaAround` has already been applied by the time anything reaches here, so the
 * five-place reading the device produced does not outlive the function that asked for it —
 * `locationArea`'s argument, kept true of this path as it is of the commit's. A club goes as its
 * id; the server rounds its point to the same cell
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §10).
 *
 * Nothing comes back. The route answers `204` whether the cell moved or not, and the caller
 * has nothing to draw: every distance to a club and every club search's order follow the cell
 * on their next read.
 */

import { changeLocation as putLocation } from '../api/playerProfileApi';
import type { LocationSource } from '../domain/ProfileDraft';
import { toWireLocation } from '../mappers/playerProfileMappers';

export function changeLocation(source: LocationSource): Promise<void> {
  return putLocation(toWireLocation(source));
}
