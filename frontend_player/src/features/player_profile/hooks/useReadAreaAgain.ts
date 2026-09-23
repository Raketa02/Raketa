/**
 * **Read my area again** — the location step's press, ending in the cold start's route
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2; [ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6 — *a person pressing a control sends the same request*).
 *
 * The press is `useLocationCapture`'s, exactly as the step's is: ask at the moment of the
 * press, read one fix, coarsen it, and hand the cell on. What differs is the last line — the
 * cell goes to `PUT /players/me/location` rather than into a draft. A fix that rounds to the
 * cell already held records nothing and answers `204`, so there is no comparison to make on
 * this side; the write is the write.
 *
 * ## Nothing is read unasked
 *
 * The step re-reads on arrival and on foreground; this does not. The cold-start refresh
 * already moves the area on a launch and after a day away, and a screen a player opened to
 * press a control should not press it for them. So the permission states here are reached by
 * the press alone, which is the step's three states minus its silent path.
 *
 * ## The write is a mutation, like the cold start's
 *
 * `useMutation` for the query client's own reason — paused offline and resumed on reconnect —
 * and, unlike the cold start's, its failure is **drawn**: somebody pressed this one. The
 * profile surface is invalidated on success as the cold start invalidates it: the read carries
 * no area today, and the invalidation is what makes it follow the day it does.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import type { AppError } from '@/shared/errors';

import type { LocationArea } from '../domain/ProfileDraft';
import { changeLocation } from '../use-cases/changeLocation';

import { playerProfileKeys } from './playerProfileKeys';
import { useLocationCapture } from './useLocationCapture';

export function useReadAreaAgain() {
  const client = useQueryClient();

  const put = useMutation<void, AppError, LocationArea>({
    mutationFn: (area) => changeLocation(area),
    onSuccess: () => client.invalidateQueries({ queryKey: playerProfileKeys.surface() }),
  });

  const { mutate } = put;
  const record = useCallback((area: LocationArea) => mutate(area), [mutate]);
  const { standing, capture } = useLocationCapture(record);

  return {
    standing,
    capture,
    /** The write's own standing — landed, failed, or on its way. */
    write: put,
  };
}
