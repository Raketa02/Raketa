/**
 * May this player be dropped straight into this sport's questionnaire?
 *
 * The decision is `admissionTo`'s, a pure rule with its own tests; this is the wiring that
 * acts on it — the same split the entry gate uses, and the same one `useAdvanceThroughPass`
 * uses. What crosses the feature's public surface is the answer, never the store.
 *
 * **Beginning happens here, and it happens during render.** A run resumed with no pass is
 * a pass of one sport, and the chrome reads a position on the questionnaire's very first
 * render — so an effect would flush too late and the screen would draw a bar it had no
 * pass to measure. Doing it from the entry gate was rejected for the same reason: its
 * redirect fires before an effect would run.
 *
 * **The answer is settled once per mount.** Beginning changes the pass the answer was
 * computed from, so re-deriving it every render would be reading the consequence of the
 * decision as though it were the input. Settling it also means a pass ending elsewhere
 * cannot turn a mounted questionnaire into a redirect underneath the player.
 */

import { useRef } from 'react';

import type { Sport } from '../domain/Sport';
import { admissionTo } from '../domain/onboardingPass';
import { useOnboardingPass } from '../store/onboardingPass.store';

/** `start-over` means welcome — see `admissionTo` for why not the entry gate. */
export type OnboardingAdmission = 'admit' | 'start-over';

/**
 * @param sport the route's validated sport, or `undefined` when the link did not survive
 * validation. Accepting `undefined` keeps this callable before the route's own guard,
 * because a hook may not be conditional.
 */
export function useOnboardingAdmission(sport: Sport | undefined): OnboardingAdmission {
  const pass = useOnboardingPass((state) => state.pass);
  const beginIfAbsent = useOnboardingPass((state) => state.beginIfAbsent);
  const settled = useRef<OnboardingAdmission>();

  if (settled.current === undefined) {
    if (sport === undefined) {
      // The route is redirecting on its own account; this answer is never read.
      settled.current = 'start-over';
    } else {
      const admission = admissionTo(pass, sport);
      if (admission.kind === 'begin') beginIfAbsent([sport]);
      settled.current = admission.kind === 'start-over' ? 'start-over' : 'admit';
    }
  }

  return settled.current;
}
