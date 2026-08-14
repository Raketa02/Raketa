/**
 * Is any assessment unfinished?
 *
 * **This is one question to the player and four requests to the server**, because
 * `GET /assessments/in-progress` is scoped to a sport — each sport is isolated, and there
 * is no collection form of the route. The fan-out is here rather than in a hook so that
 * the gate reads it as the single query it conceptually is, and so the cost is written
 * down in one place: four parallel reads on a cold launch.
 *
 * If that cost becomes a problem the fix is a collection endpoint on the backend, not a
 * cache in the client — a client that remembered "no run in progress" would strand a
 * player who started one on another device.
 *
 * The requests go out together, and the answer is the first run in registry order so that
 * two unfinished runs resolve the same way every launch.
 */

import type { AssessmentRun } from '../domain/Assessment';
import { SPORTS, type Sport } from '../domain/Sport';
import { findInProgress } from '../api/onboardingApi';
import { toAssessmentRun, toWireSport } from '../mappers/onboardingMappers';

export interface FindRunInProgressOptions {
  readonly signal?: AbortSignal;
}

export async function findRunInProgress({ signal }: FindRunInProgressOptions = {}): Promise<
  AssessmentRun | undefined
> {
  const found = await Promise.all(SPORTS.map((sport) => runFor(sport, signal)));

  return found.find((run): run is AssessmentRun => run !== undefined);
}

async function runFor(
  sport: Sport,
  signal: AbortSignal | undefined,
): Promise<AssessmentRun | undefined> {
  // 204 — no run for this sport — decodes to `undefined`, which is an answer rather than
  // a failure.
  const step = await findInProgress(toWireSport(sport), { signal });
  return step === undefined ? undefined : toAssessmentRun(step, sport);
}
