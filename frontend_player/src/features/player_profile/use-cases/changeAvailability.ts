/**
 * Make this the player's week.
 *
 * **The week as the profile now holds it comes back**, and that is what a caller may draw: the
 * write path collapses repeated cells and answers in the platform's own reading order, so a
 * client that kept what it sent would hold a week the profile does not — the same discipline
 * the radius write runs, where the response carries the distance after the range and the step
 * were re-checked.
 *
 * **A cleared week is a value and not a refusal.** `AvailabilityGridEmpty` binds the commit at
 * the end of onboarding, which is the answer a player is *asked for*; a player who unticks
 * every cell afterwards has said something legal, and the matcher reads a blank grid as
 * *absent* rather than as a zero
 * ([ADR-0102](../../../../../docs/adr/0102-silence-is-never-scored.md)).
 *
 * It is the route `KEEP_THESE_TIMES` is answered through, and the answering is a **write of
 * the week the search ran on** — the prompt's own payload, never a week this app composed.
 */

import type { WeekCell } from '@/shared/vocabulary/week';

import { changeAvailability as putAvailability } from '../api/playerProfileApi';
import { toWeekCells, toWireSlots } from '../mappers/playerProfileMappers';

export function changeAvailability(week: readonly WeekCell[]): Promise<readonly WeekCell[]> {
  return putAvailability({ availability: toWireSlots(week) }).then((response) =>
    toWeekCells(response.availability),
  );
}
