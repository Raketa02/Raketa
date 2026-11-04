/**
 * **Is any assessment unfinished?** — the first run in the server's order, `null` for none.
 *
 * It was the entry gate's read, and the gate resumed what it answered. Nothing resumes a run on
 * launch any more ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §5, [#730](https://github.com/Raketa02/Raketa/issues/730)), so its one reader is the door where
 * play begins, which offers the run as *Carry on*. Same key, same `queryFn`: a start marks it stale,
 * an answer that ends the run and a completion invalidate it, and an abandonment removes it.
 *
 * `?? null` is load-bearing. TanStack Query reserves `undefined` for "nothing cached" and rejects
 * it as data, so a query that answered "no run in progress" by returning `undefined` would be
 * recorded as a failed fetch. `null` is the value that means *asked, and there is none*.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { AssessmentRun } from '../domain/Assessment';
import { findRunInProgress } from '../use-cases/findRunInProgress';

import { onboardingKeys } from './onboardingKeys';

export function useRunInProgress() {
  return useQuery<AssessmentRun | null, AppError>({
    queryKey: onboardingKeys.runInProgress(),
    queryFn: ({ signal }) => findRunInProgress({ signal }).then((found) => found ?? null),
  });
}
