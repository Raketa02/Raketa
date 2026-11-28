/**
 * **Is a questionnaire in this sport left halfway, and on which question?** — for a door about one
 * sport, which says *Carry on* in place of its start ([#765](https://github.com/Rakieta02/Rakieta/issues/765):
 * a friend's ask for a level on Home, *Carry on* and *You're on question 5.*).
 *
 * The door where play begins answers the same question about **any** sport (`useLevelDoor`, the
 * first unfinished run); this one answers it about the door's own, off every unfinished run
 * (`onboardingKeys.runsInProgress`) and that run's own step, and counts the question as that door
 * does (`levelDoor`): the answered ones and the one outstanding.
 *
 * **`undefined` until a run in the sport is known** — none, still being read, or not readable.
 * Unlike the door where play begins, which waits to know before it draws, a door about one sport
 * can draw its start at once: its start and its *Carry on* are **one act** (`useAddASport`'s `rate`
 * — the server answers a sport already being rated with its outstanding run), so a press before
 * the read lands opens the same run the word would have named.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import type { AssessmentRun } from '../domain/Assessment';
import { levelDoor } from '../domain/levelDoor';
import { findRunsInProgress } from '../use-cases/findRunInProgress';

import { onboardingKeys } from './onboardingKeys';
import { assessmentQuery } from './useAssessment';

export function useQuestionLeftAt(sport: Sport): number | undefined {
  const runs = useQuery<readonly AssessmentRun[], AppError>({
    queryKey: onboardingKeys.runsInProgress(),
    queryFn: ({ signal }) => findRunsInProgress({ signal }),
  });
  const run = runs.data?.find((one) => one.sport === sport);
  const step = useQuery({
    ...assessmentQuery(run?.assessmentId ?? ''),
    enabled: run !== undefined,
  });

  if (run === undefined || step.data === undefined) return undefined;
  const offer = levelDoor(run, step.data);
  return offer.kind === 'carry-on' ? offer.question : undefined;
}
