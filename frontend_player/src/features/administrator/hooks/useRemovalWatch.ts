/**
 * **Removed while here** — the club took this person's administrator profile away while the area
 * was open (PRD #500 story 136, ADR-0184 §7; [#516](https://github.com/Rakieta02/Rakieta/issues/516)).
 *
 * The backend asks again on **every** administrator request, so a removal lands as
 * `403 not_an_administrator` on whichever request the area makes next — the Groups tab's read, a
 * page, a create, an answer. So the watch is not on any one of them: it listens to **every query
 * and mutation under this feature's keys**, and answers the first such refusal once.
 *
 * What it answers is the caller's (`onRemoved`), because what a removal means depends on what else
 * the account holds: an account that only administers has nowhere left to be and is signed out;
 * one that also plays is moved to its player side, which is the profile switcher's
 * ([#518](https://github.com/Rakieta02/Rakieta/issues/518)).
 *
 * A cache subscription rather than an `onError` on each hook: queries have no `onError` in this
 * Query, and a rule restated on five hooks is the one the sixth forgets.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';

import { isAppError } from '@/shared/errors';

import { administratorKeys } from './administratorKeys';

/** The one code a removed Administrator's next request is refused with. */
const REMOVED = 'not_an_administrator';

/** Whether a failure says this account no longer runs this club's groups. */
export function isRemoval(error: unknown): boolean {
  return isAppError(error) && error.code === REMOVED;
}

function underThisFeature(key: readonly unknown[] | undefined): boolean {
  return key?.[0] === administratorKeys.all[0];
}

export function useRemovalWatch(onRemoved: () => void): void {
  const client = useQueryClient();
  const fired = useRef(false);
  // The latest callback, without re-subscribing on every render that makes a new one.
  const latest = useRef(onRemoved);
  latest.current = onRemoved;

  useEffect(() => {
    const answer = (key: readonly unknown[] | undefined, error: unknown) => {
      if (fired.current || !underThisFeature(key) || !isRemoval(error)) return;
      fired.current = true;
      latest.current();
    };

    const offQueries = client.getQueryCache().subscribe((event) => {
      if (event.type === 'updated' && event.action.type === 'error') {
        answer(event.query.queryKey, event.action.error);
      }
    });
    const offMutations = client.getMutationCache().subscribe((event) => {
      if (event.type === 'updated' && event.action.type === 'error') {
        answer(event.mutation.options.mutationKey, event.action.error);
      }
    });

    return () => {
      offQueries();
      offMutations();
    };
  }, [client]);
}
