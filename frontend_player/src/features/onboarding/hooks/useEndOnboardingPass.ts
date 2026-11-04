/**
 * Ending an onboarding pass, at the one place it is definitional.
 *
 * **A pass is over when the player is in the app.** Not when the done screen unmounts, not
 * when the data screen's continue is pressed, not when the picker next opens — those are
 * exits, and there are several, and a rule spread over several exits is a rule that gets a
 * new exit added without it. Being in the app is the *definition*, so this is one call on
 * the entry gate's app branch.
 *
 * Before it existed, nothing declared that a walk had ended. The picker cleared one store
 * of the three on the stated assumption that nothing else reaches onboarding twice in one
 * launch — which the gate's own resume path already broke, because it redirects straight to
 * an outstanding question with no picker in between. A player who rated two sports, entered
 * the app and then resumed an unfinished run was still inside the first walk as far as the
 * app was concerned, and read "Rating 2 of 2" for a single run.
 *
 * **Ending is allowed to be lazy.** Nothing reads a pass once the player is in the app, so
 * an effect is soon enough. Beginning is the half that cannot be — the question screen
 * reads a position on its first render — which is why beginning is not done from here.
 *
 * ## The ended pass is read once, for where it began
 *
 * A pass has an origin, and where it ends is read off it
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3): a pass begun at the Skill passport's *Add a sport* ends **on the passport**, and the
 * passport is a screen inside the app. Every way out of that pass — *See your ratings*, the
 * leave sheet's *continue later*, its *abandon* — enters the app exactly as a welcome pass
 * does, and it is this branch, on ending the pass, that lands it: the origin is handed to
 * the caller, and the caller — a route file — turns it into a route. Landing from here
 * rather than from the three exits is the same argument as ending from here: one site, and
 * the definition rather than a line to remember on each way out. And it is why the store's
 * `end` *returns* the pass rather than this hook subscribing to it — a gate that re-rendered
 * on every change to the pass would end the one the chip has just begun, before the
 * questionnaire mounted.
 *
 * **A pass begun on a group lands the same way** (ADR-0200 §5): back on that group, on the tab
 * it began on, with the chip on the sport rated last — `returnOf` says which, and the route
 * file turns it into the group's route.
 *
 * A deferred run is untouched by this. Its lifetime is the app session, and reaching the
 * app is exactly the moment a deferral has to survive.
 */

import { useEffect, useRef } from 'react';

import { returnOf, type PassReturn } from '../domain/onboardingPass';
import { useOnboardingPass } from '../store/onboardingPass.store';

/**
 * What the app does with a pass that has just ended, told where to put it back (`returnOf`):
 * the passport, or a group on its tab with the sport rated last. Called once per pass, and
 * never for a welcome pass, from the gate's app branch, after the authenticated tree has
 * mounted — so a caller that navigates inside the tree finds the shell there to navigate.
 */
export type PassLanding = (back: PassReturn) => void;

/**
 * @param inTheApp whether the entry gate has landed the player in the authenticated tree.
 * Passed rather than read here so the gate keeps one answer, and the caller stays a route
 * file that turns a decision into a route.
 * @param land where the app puts a player whose pass just ended, by the pass's origin.
 */
export function useEndOnboardingPass(inTheApp: boolean, land: PassLanding): void {
  const end = useOnboardingPass((state) => state.end);

  // The latest landing, read at the moment of ending rather than closed over: a landing that
  // reads the current path is a new function per render, and an effect keyed on it would
  // re-run on every render of the gate — harmlessly, since a second `end` finds nothing, but
  // the effect's one job is to fire on *arriving*, and its dependencies should say so.
  const landing = useRef(land);
  landing.current = land;

  useEffect(() => {
    if (!inTheApp) return;
    const ended = end();
    const back = ended === undefined ? undefined : returnOf(ended);
    if (back !== undefined) landing.current(back);
  }, [inTheApp, end]);
}
