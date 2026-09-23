/**
 * Move the player's Location area to where the phone is.
 *
 * **The only way a location moves after onboarding**, and it takes the **area**, never the
 * fix: `areaAround` has already been applied by the time anything reaches here, so the
 * five-place reading the device produced does not outlive the function that asked for it —
 * `locationArea`'s argument, kept true of this path as it is of the commit's.
 *
 * Nothing comes back. The route answers `204` whether the cell moved or not, and the caller
 * has nothing to draw: the deck's next hand deals around the new cell, the radar refetches on
 * its own rule, and *In your area* follows the projection
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6).
 */

import { changeLocation as putLocation } from '../api/playerProfileApi';
import type { LocationArea } from '../domain/ProfileDraft';

export function changeLocation(area: LocationArea): Promise<void> {
  return putLocation({ latitude: area.latitude, longitude: area.longitude });
}
