/**
 * Is any assessment unfinished?
 *
 * **One question to the player, and now one request to the server.** The collection form of
 * `GET /assessments/in-progress` answers for every sport at once, so the fan-out this used
 * to be — four parallel per-sport reads on every cold launch, for an answer that is almost
 * always "no" — is gone.
 *
 * The answer is the first run the server sent. Entries come back in sport-registry order,
 * which is `SPORTS`' order, so "first in registry order" is the first entry and two
 * unfinished runs still resolve the same way on every launch. That ordering is the
 * contract's, and this client does not restate it.
 *
 * An empty collection means no run in progress. It is the ordinary answer and never an
 * error path.
 *
 * Nothing here is cached beyond the query above it: a client that remembered "no run in
 * progress" would strand a player who started one on another device, which is the case
 * resume exists for.
 */

import type { AssessmentRun } from '../domain/Assessment';
import { listRunsInProgress } from '../api/onboardingApi';
import { toAssessmentRuns } from '../mappers/onboardingMappers';

export interface FindRunInProgressOptions {
  readonly signal?: AbortSignal;
}

export async function findRunInProgress({ signal }: FindRunInProgressOptions = {}): Promise<
  AssessmentRun | undefined
> {
  const runs = toAssessmentRuns(await listRunsInProgress({ signal }));

  return runs[0];
}
