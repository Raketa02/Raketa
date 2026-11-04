/**
 * **Where you play's two writes** — the location step's press, and a club picked in its place,
 * each ending in the cold start's route
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2; [ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6 — *a person pressing a control sends the same request*;
 * [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §10 — *You ›
 * Where you play offers both ways*).
 *
 * The press is `useLocationCapture`'s, exactly as the step's is: ask at the moment of the
 * press, read one fix, coarsen it, and hand the cell on. A pick hands the club on. What differs
 * from the step is the last line — either goes to `PUT /players/me/location` rather than into a
 * draft. A cell already held records nothing and answers `204`, so there is no comparison to
 * make on this side; the write is the write.
 *
 * ## Nothing is read unasked
 *
 * The step re-reads on arrival and on foreground; this does not. The cold-start refresh
 * already moves the area on a launch and after a day away, and a screen a player opened to
 * press a control should not press it for them. So the permission states here are reached by
 * the press alone, which is the step's three states minus its silent path.
 *
 * ## One write, so the latest answer is the one on screen
 *
 * Both controls go through one `useMutation`, for the query client's own reason — paused
 * offline and resumed on reconnect — and so that **what the screen draws is the write it
 * last sent**: the mutation's variables are the reading or the club, and a reading pressed after
 * a pick replaces the pick on screen as it replaces it on the server. The writes share a `scope`
 * with the cold start's (`LOCATION_WRITES`), so they land in the order they were sent. What the
 * screen draws is read off that one write here — `readingSaved`, `chosenClub` and the two busy
 * states — so the screen holds no rule of its own. Unlike the cold start's, a failure is
 * **drawn**: somebody pressed this one. The profile surface is invalidated on success as the cold
 * start invalidates it.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import type { AppError } from '@/shared/errors';

import type { LocationArea, LocationSource, PickedClub } from '../domain/ProfileDraft';
import { changeLocation } from '../use-cases/changeLocation';

import { LOCATION_WRITES, playerProfileKeys } from './playerProfileKeys';
import { useLocationCapture } from './useLocationCapture';

export function useChangeArea() {
  const client = useQueryClient();

  const write = useMutation<void, AppError, LocationSource>({
    mutationFn: changeLocation,
    // In line with the cold start's write and with each other: pressed in order, landed in order.
    scope: LOCATION_WRITES,
    onSuccess: () => client.invalidateQueries({ queryKey: playerProfileKeys.surface() }),
  });

  const { mutate, reset } = write;
  const record = useCallback((area: LocationArea) => mutate({ kind: 'reading', area }), [mutate]);
  const { standing, capture } = useLocationCapture(record);

  const pick = useCallback((club: PickedClub) => mutate({ kind: 'club', club }), [mutate]);

  const sent = write.variables;

  return {
    standing,
    capture,
    pick,
    /** *Change*: the club is let go of on screen and the search comes back. Nothing is written. */
    letGoOfClub: reset,
    /** The phone's cell has landed, and nothing is being read now — *Location saved*. */
    readingSaved: write.isSuccess && sent?.kind === 'reading' && !standing.reading,
    /** The phone is being read, or its cell is on its way — the control is busy. */
    readingOnItsWay: standing.reading || (write.isPending && sent?.kind === 'reading'),
    /** The club on its way or landed. A refused write lets go of it, so the search comes back. */
    chosenClub: sent?.kind === 'club' && !write.isError ? sent.club : undefined,
    /** A pick is on its way — *Change* says *Saving…*, and the ground is not yet mint. */
    savingClub: write.isPending && sent?.kind === 'club',
    /** Why the last write was refused, or `null`. */
    error: write.error,
  };
}
