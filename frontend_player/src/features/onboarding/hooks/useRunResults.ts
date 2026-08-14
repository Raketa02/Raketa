/**
 * Every rating this onboarding pass produced, read back.
 *
 * The runs are the pass's — which assessments, and which sports — and the *ratings* are
 * Query's, read through the same key and the same `queryFn` the result screen used. So the
 * done screen ordinarily performs no request at all: it is showing what the player has
 * just been shown, one card each, out of the cache it was shown from.
 *
 * It still degrades correctly when it is not there. An unused query is collected after five
 * minutes, so a player who spent long enough on the second sport finds the first refetched
 * rather than missing — which is the whole reason this reads a cache rather than a
 * snapshot taken when the result screen happened to be mounted.
 *
 * One query per run rather than one request for the collection: `GET /ratings` answers what
 * this player is rated at, which is a different question with a different answer for anyone
 * who arrived here with a rating already.
 */

import { useQueries, type UseQueryResult } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { AssessmentStep } from '../domain/Assessment';
import type { RatedRun } from '../domain/onboardingPass';

import { assessmentQuery } from './useAssessment';

export interface RunResult {
  readonly run: RatedRun;
  readonly query: UseQueryResult<AssessmentStep, AppError>;
}

export function useRunResults(runs: readonly RatedRun[]): readonly RunResult[] {
  const results = useQueries({
    queries: runs.map((run) => assessmentQuery(run.assessmentId)),
  });

  // Zipped here rather than by index at the call site: `noUncheckedIndexedAccess` makes
  // every `results[i]` an optional, and a screen inventing a branch for a card whose
  // query cannot be missing is a branch nothing can test.
  //
  // The error cast is the same one the entry gate makes, for the same reason: everything
  // reaching a `queryFn` in this app is normalised by the http client, so an error here is
  // an `AppError` — `useQueries` simply has nowhere to be told so.
  return runs.map((run, index) => ({
    run,
    query: results[index] as UseQueryResult<AssessmentStep, AppError>,
  }));
}
