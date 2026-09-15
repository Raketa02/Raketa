/**
 * The location step's orchestration: ask, read one fix, coarsen it, and keep it current.
 *
 * **Nothing here decides anything.** What an area *is* — two decimal places, and why that
 * and not three — is `locationArea`'s, with its own tests and no renderer. What is left is
 * the sequencing a screen cannot express: asking the OS at the moment the player pressed
 * something, reading a single position, and re-reading it when the app comes back.
 *
 * ## One fix, on purpose, and never a subscription
 *
 * Every path here ends in `readFix()`. Nothing watches, nothing polls, and the port offers
 * no way to do either — a stream of positions is a movement trail, which is a different
 * privacy class from the one the player was asked about. The re-read on foreground is the
 * same single fix asked for again, at the one moment the answer could have gone stale
 * without anybody looking.
 *
 * ## The precise fix does not survive this file
 *
 * `areaAround` is applied to the reading before it goes anywhere. Nothing above this hook
 * ever holds latitude to five decimal places, so no screen can render it and no store can
 * leak it — which is what makes *the precise fix is never stored* a fact about the code
 * rather than a promise about intentions.
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
 * is not held hostage on step five of eight by a permission they can change at any time.
 */

import { useCallback, useEffect, useState } from 'react';

import {
  ensurePermission,
  useLocation,
  useOnForeground,
  type PermissionState,
} from '@/shared/lib/platform';

import type { LocationArea } from '../domain/ProfileDraft';
import { areaAround, sameArea } from '../domain/locationArea';
import { useProfileDraft } from '../store/profileDraft.store';

/**
 * What the step may say about the device, which is less than the OS distinguishes.
 *
 * `unasked` is not a permission state — it is *nobody has pressed anything yet*, and it is
 * what stops the screen scolding a player who has done nothing wrong. `undetermined` and
 * `denied` collapse into `refused` for the reason the photos step gives: the only sentence
 * either could carry is *press again*, and it is the same sentence.
 */
export type LocationAccess = 'unasked' | 'granted' | 'refused' | 'blocked';

export interface LocationStepStanding {
  readonly access: LocationAccess;
  /** A fix is being read. The control says so rather than going quiet. */
  readonly reading: boolean;
  /** Allowed, asked, and the device still produced nothing. */
  readonly noFix: boolean;
}

const UNASKED: LocationStepStanding = { access: 'unasked', reading: false, noFix: false };

function accessFrom(permission: PermissionState): LocationAccess {
  if (permission === 'granted') return 'granted';
  return permission === 'blocked' ? 'blocked' : 'refused';
}

export function useLocationStep() {
  const location = useLocation();
  const area = useProfileDraft((state) => state.draft?.location);
  const answer = useProfileDraft((state) => state.answer);
  const [standing, setStanding] = useState<LocationStepStanding>(UNASKED);

  /**
   * Write the area, unless it is the one already held.
   *
   * The draft is read from the store rather than from the render that started the read: a
   * fix arrives whenever the device produces it, and the closure that asked for it may be
   * two renders old by then.
   */
  const record = useCallback(
    (fresh: LocationArea) => {
      if (sameArea(useProfileDraft.getState().draft?.location, fresh)) return;
      answer({ location: fresh });
    },
    [answer],
  );

  const readOneFix = useCallback(async () => {
    const fix = await location.readFix();
    // The reading is coarsened here and the fix goes out of scope with this function.
    if (fix !== null) record(areaAround(fix.latitude, fix.longitude));
    return fix !== null;
  }, [location, record]);

  /**
   * What the player presses. The only path in this file that may show the OS prompt.
   */
  const capture = useCallback(async () => {
    setStanding({ access: 'unasked', reading: true, noFix: false });

    const permission = await ensurePermission(location);
    if (permission !== 'granted') {
      setStanding({ access: accessFrom(permission), reading: false, noFix: false });
      return;
    }

    const placed = await readOneFix();
    setStanding({ access: 'granted', reading: false, noFix: !placed });
  }, [location, readOneFix]);

  /**
   * A fix without a prompt, for the two moments the player did not ask for one: arriving on
   * the step with the permission already granted, and coming back to the app.
   *
   * A failed read is left in silence here. The player asked for nothing, so there is nothing
   * to report — and blanking or scolding over an area that is already on screen would make
   * a walk past a basement look like something the player did.
   */
  const refresh = useCallback(async () => {
    if ((await location.getPermission()) !== 'granted') return;
    // Being allowed is worth holding even when the read comes back empty: it is what stops
    // the screen telling a player whose phone has already been asked and answered that
    // nothing is read until they press. `noFix` is deliberately left alone — a silent read
    // that found nothing is not something to report.
    setStanding((held) => (held.access === 'granted' ? held : { ...held, access: 'granted' }));
    await readOneFix();
  }, [location, readOneFix]);

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
