/**
 * Make this the player's week.
 *
 * **The week as the profile now holds it comes back**, and that is what a caller may draw: the
 * write path collapses repeated hours and answers in the platform's own reading order, so a
 * client that kept what it sent would hold a week the profile does not — the same discipline
 * the radius write runs, where the response carries the distance after the range and the step
 * were re-checked.
 *
 * **A cleared week is a value and not a refusal.** `WeeklyHoursEmpty` binds the commit at
 * the end of onboarding, which is the answer a player is *asked for*; a player who unticks
 * every hour afterwards has said something legal, and the matcher reads a blank week as
 * *absent* rather than as a zero
 * ([ADR-0102](../../../../../docs/adr/0102-silence-is-never-scored.md)).
 *
 * It is the route `KEEP_THESE_TIMES` is answered through, and the answering is a **write of
 * the week the search ran on** — the prompt's own payload, never a week this app composed.
 */

import type { WeeklyHour } from '@/shared/vocabulary/week';

import { changeWeeklyHours as putWeeklyHours } from '../api/playerProfileApi';
import { toWeeklyHours, toWireWeeklyHours } from '../mappers/playerProfileMappers';

export function changeWeeklyHours(week: readonly WeeklyHour[]): Promise<readonly WeeklyHour[]> {
  return putWeeklyHours({ weeklyHours: toWireWeeklyHours(week) }).then((response) =>
    toWeeklyHours(response.weekly_hours),
  );
}
