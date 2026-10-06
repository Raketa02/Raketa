/**
 * The **Location area**: a device's fix, coarsened, and the only form of it this app keeps.
 *
 * The glossary's invariant is that *a location is held coarsely, and the precise fix is
 * never stored* (`../../../../../CONTEXT.md`). The backend makes that true of its event
 * store by rounding on the way in (`player_profile/domain/location.py`); this module makes
 * it true of the phone. **The coarsening happens the moment the fix is read**, before
 * anything is written to the draft and before anything is drawn, so there is no state in
 * this app — not a store, not a screen, not a render — that holds the metres the device
 * reported.
 *
 * That is the same argument in both places and it is not redundant work. A precise fix that
 * is held for the length of a step is a precise fix that is in a crash report, a state
 * snapshot and whatever a future screen decides to render; a fix that was discarded on
 * arrival cannot be. The honest way to not hold something is to not hold it.
 *
 * ## Two decimal places, and deliberately not three
 *
 * Two is about 1,1 km of latitude and less of longitude away from the equator — the
 * resolution the platform's distances are expressed in, which is whole kilometres. A finer
 * location would be precision no consumer can use, bought with a fact about the
 * player nobody needed. The number matches the backend's `LOCATION_PRECISION_DP` because it
 * is the same decision, not because one copied the other: rounding twice at the same
 * resolution is a no-op, which is what lets the rule live at both ends without the second
 * one moving the answer.
 */

import type { LocationArea } from './ProfileDraft';

/** Decimal places kept. See above — this is a distance's own resolution, not one better. */
export const LOCATION_AREA_DECIMALS = 2;

/**
 * The area a fix falls in. **The fix itself is discarded here** and never leaves this call.
 *
 * Plain numbers rather than the platform's `LocationFix`, because a rule in `domain/` is
 * pure and knows nothing about the device — and because the type also carries an accuracy,
 * which is a claim about the reading and has no meaning once the reading is gone.
 */
export function areaAround(latitude: number, longitude: number): LocationArea {
  return {
    latitude: onTheGrid(latitude),
    longitude: onTheGrid(longitude),
  };
}

/**
 * Whether both sides are the same answer — two areas, or two absences.
 *
 * Asked before recording, so a foreground re-read that lands in the area already held
 * writes nothing. Without it every return to the app would replace the draft with an
 * identical one, which is a redraw of every step that reads it and a change nothing
 * changed.
 */
export function sameArea(one: LocationArea | undefined, other: LocationArea | undefined): boolean {
  if (one === undefined || other === undefined) return one === other;
  return one.latitude === other.latitude && one.longitude === other.longitude;
}

function onTheGrid(degrees: number): number {
  return Number(degrees.toFixed(LOCATION_AREA_DECIMALS));
}
