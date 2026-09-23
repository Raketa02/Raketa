/**
 * Ask, read one fix, coarsen it, hand it on — **the press, without the step around it.**
 *
 * Two screens press a control that reads the phone: the location step, which puts the area
 * into the part's draft, and the You tab's *Where you play*, which puts it to
 * `PUT /players/me/location` ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2 — *the location's route is the cold start's, and a person pressing a control sends the
 * same request*). What the press does is identical up to the last line, so it is here once
 * and the last line is the caller's.
 *
 * ## One fix, on purpose, and never a subscription
 *
 * Every path here ends in `readFix()`. Nothing watches, nothing polls, and the port offers no
 * way to do either — a stream of positions is a movement trail, which is a different privacy
 * class from the one the player was asked about.
 *
 * ## The precise fix does not survive this file
 *
 * `areaAround` is applied to the reading before it goes anywhere. Nothing above this hook ever
 * holds latitude to five decimal places, so no screen can render it and no store can leak it —
 * which is what makes *the precise fix is never stored* a fact about the code rather than a
 * promise about intentions.
 *
 * ## Asking is the player's move; a silent re-read is not
 *
 * `capture` is the only path that may show the OS prompt, and it runs when the control is
 * pressed. `refresh` is the fix without a prompt — `getPermission()` only — for the two
 * moments the step re-reads on its own, arriving and coming back to the app; **it is offered
 * and not scheduled**, because whether a screen re-reads unasked is that screen's rule. The
 * step does; the tab does not, since the cold-start refresh already moves the area and a
 * screen a player opened to press a control should not press it for them.
 */

import { useCallback, useState } from 'react';

import { ensurePermission, useLocation, type PermissionState } from '@/shared/lib/platform';

import type { LocationArea } from '../domain/ProfileDraft';
import { areaAround } from '../domain/locationArea';

/**
 * What the screen may say about the device, which is less than the OS distinguishes.
 *
 * `unasked` is not a permission state — it is *nobody has pressed anything yet*, and it is
 * what stops the screen scolding a player who has done nothing wrong. `undetermined` and
 * `denied` collapse into `refused` for the reason the photos step gives: the only sentence
 * either could carry is *press again*, and it is the same sentence.
 */
export type LocationAccess = 'unasked' | 'granted' | 'refused' | 'blocked';

export interface LocationStanding {
  readonly access: LocationAccess;
  /** A fix is being read. The control says so rather than going quiet. */
  readonly reading: boolean;
  /** Allowed, asked, and the device still produced nothing. */
  readonly noFix: boolean;
}

const UNASKED: LocationStanding = { access: 'unasked', reading: false, noFix: false };

function accessFrom(permission: PermissionState): LocationAccess {
  if (permission === 'granted') return 'granted';
  return permission === 'blocked' ? 'blocked' : 'refused';
}

/**
 * @param record what a coarse area is for — the draft on the step, the route on the tab. Called
 *   with the cell and never the fix.
 */
export function useLocationCapture(record: (area: LocationArea) => void) {
  const location = useLocation();
  const [standing, setStanding] = useState<LocationStanding>(UNASKED);

  const readOneFix = useCallback(async () => {
    const fix = await location.readFix();
    // The reading is coarsened here and the fix goes out of scope with this function.
    if (fix !== null) record(areaAround(fix.latitude, fix.longitude));
    return fix !== null;
  }, [location, record]);

  /** What the player presses. The only path in this file that may show the OS prompt. */
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
   * A fix without a prompt, for a moment the player did not ask for one.
   *
   * A failed read is left in silence here. The player asked for nothing, so there is nothing
   * to report — and blanking or scolding over an area that is already on screen would make a
   * walk past a basement look like something the player did.
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

  return { standing, capture, refresh };
}
