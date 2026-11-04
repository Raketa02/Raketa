/**
 * The location step's orchestration: ask, read one fix, coarsen it, and keep it current — or
 * take a club picked in its place.
 *
 * **Nothing here decides anything.** What an area *is* — two decimal places, and why that
 * and not three — is `locationArea`'s, with its own tests and no renderer. The press itself —
 * asking the OS at the moment the player pressed something, reading a single position,
 * coarsening it — is `useLocationCapture`'s, shared with the You tab's *Where you play*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2). What is left here is the step's own rules: **where the area goes**, **when it is
 * re-read unasked**, and **what stands in for a refused reading**.
 *
 * ## The area goes to the draft, unless it is the one already held
 *
 * The draft is read from the store rather than from the render that started the read: a fix
 * arrives whenever the device produces it, and the closure that asked for it may be two
 * renders old by then. **A reading replaces a picked club**: once the phone may be read, its
 * cell is the truer answer (ADR-0200 §10), so a foreground re-read after the permission was
 * allowed in Settings moves the draft off the club.
 *
 * ## Asking is the player's move; re-reading is not
 *
 * The first prompt happens when the control is pressed, never on arrival, because the
 * sentence that earns a yes has to be read first. The mount and the foreground re-read use
 * `getPermission()` only: a return to the app is not a press, and a player who refused must
 * not find the OS dialog waiting each time they come back.
 *
 * ## A refusal is answered with a club, and the step still requires an area
 *
 * Every distance to a club is measured from the area, so the step does not let a player past
 * without one ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §10). A refusal — denied, blocked, or no fix — is answered by *Pick a club near where you
 * play*: `pick` puts the club in the draft as the area, and `unpick` takes it out again so the
 * search is offered afresh. Apple's 5.1.1(iv) asks for exactly this other way.
 */

import { useCallback, useEffect } from 'react';

import { useOnForeground } from '@/shared/lib/platform';

import type { LocationArea, PickedClub } from '../domain/ProfileDraft';
import { sameArea } from '../domain/locationArea';
import { useProfileDraft } from '../store/profileDraft.store';

import { useLocationCapture } from './useLocationCapture';

export function useLocationStep() {
  const location = useProfileDraft((state) => state.draft?.location);
  const answer = useProfileDraft((state) => state.answer);

  const record = useCallback(
    (fresh: LocationArea) => {
      const held = useProfileDraft.getState().draft?.location;
      if (held?.kind === 'reading' && sameArea(held.area, fresh)) return;
      answer({ location: { kind: 'reading', area: fresh } });
    },
    [answer],
  );

  const pick = useCallback(
    (club: PickedClub) => answer({ location: { kind: 'club', club } }),
    [answer],
  );

  /** *Change*: the club leaves the draft, and the search is offered again. */
  const unpick = useCallback(() => answer({ location: undefined }), [answer]);

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

  return { location, standing, capture, pick, unpick };
}
