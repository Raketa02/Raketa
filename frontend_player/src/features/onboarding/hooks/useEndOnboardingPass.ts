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
 * A deferred run is untouched by this. Its lifetime is the app session, and reaching the
 * app is exactly the moment a deferral has to survive.
 */

import { useEffect } from 'react';

import { useOnboardingPass } from '../store/onboardingPass.store';

/**
 * @param inTheApp whether the entry gate has landed the player in the authenticated tree.
 * Passed rather than read here so the gate keeps one answer, and the caller stays a route
 * file that turns a decision into a route.
 */
export function useEndOnboardingPass(inTheApp: boolean): void {
  const end = useOnboardingPass((state) => state.end);

  useEffect(() => {
    if (!inTheApp) return;
    end();
  }, [inTheApp, end]);
}
