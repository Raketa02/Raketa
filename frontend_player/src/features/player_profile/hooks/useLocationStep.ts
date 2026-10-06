/**
 * The location step's orchestration: ask, read one fix, coarsen it, and keep it current.
 *
 * **Nothing here decides anything.** What an area *is* — two decimal places, and why that
 * and not three — is `locationArea`'s, with its own tests and no renderer. The press itself —
 * asking the OS at the moment the player pressed something, reading a single position,
 * coarsening it — is `useLocationCapture`'s, shared with the You tab's *Where you play*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2). What is left here is the step's two own rules: **where the area goes**, and **when it
 * is re-read unasked**.
 *
 * ## The area goes to the draft, unless it is the one already held
 *
 * The draft is read from the store rather than from the render that started the read: a fix
 * arrives whenever the device produces it, and the closure that asked for it may be two
 * renders old by then.
 *
 * ## Asking is the player's move; re-reading is not
 *
 * The first prompt happens when the control is pressed, never on arrival, because the
 * sentence that earns a yes has to be read first. The mount and the foreground re-read use
 * `getPermission()` only: a return to the app is not a press, and a player who refused must
 * not find the OS dialog waiting each time they come back.
 *
 * ## A refusal costs discovery, and it does not cost the step
 *
 * Location is what search and matchmaking are worked out from, so this step insists — but a
 * refusal still continues, without an area, and the screen says what that means. The player
 * is not held hostage on step five of six by a permission they can change at any time.
 */

import { useCallback, useEffect } from 'react';

import { useOnForeground } from '@/shared/lib/platform';

import type { LocationArea } from '../domain/ProfileDraft';
import { sameArea } from '../domain/locationArea';
import { useProfileDraft } from '../store/profileDraft.store';

import { useLocationCapture } from './useLocationCapture';

export function useLocationStep() {
  const area = useProfileDraft((state) => state.draft?.location);
  const answer = useProfileDraft((state) => state.answer);

  const record = useCallback(
    (fresh: LocationArea) => {
      if (sameArea(useProfileDraft.getState().draft?.location, fresh)) return;
      answer({ location: fresh });
    },
    [answer],
  );

  const { standing, capture, refresh } = useLocationCapture(record);

  // The two moments the player did not ask for a read: arriving on the step with the
  // permission already granted, and coming back to the app.
  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Story 58: what is on screen should be near where the player actually is, and the moment
  // it can silently stop being true is the one where they were somewhere else in between.
  useOnForeground(() => {
    void refresh();
  });

  return { area, standing, capture };
}
