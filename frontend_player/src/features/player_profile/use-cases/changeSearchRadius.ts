/**
 * Make this the player's Search radius.
 *
 * **The only way a search's reach can change.** `RunSearchRequest` carries no radius and never
 * will — *"a radius supplied by a phone is a gate evaluated on a lie"* — so the searcher's ask
 * **is** their profile radius, read at request time. A control that offered a per-search
 * distance would be a control with nowhere to send it.
 *
 * It answers with the radius **as the profile now holds it**, which is what a caller should
 * draw: the write path re-checks the range and the step, so a client that assumed its own
 * number landed would be re-deciding a rule the server owns.
 */

import { changeSearchRadius as putSearchRadius } from '../api/playerProfileApi';

export function changeSearchRadius(radiusKm: number): Promise<number> {
  return putSearchRadius({ radiusKm }).then((response) => response.search_radius_km);
}
