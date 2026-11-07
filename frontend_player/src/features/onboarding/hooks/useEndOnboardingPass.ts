/**
 * Ending a rating pass, at the one place it is definitional.
 *
 * **A pass is over when the player is in the app.** Not when the last result is left, not
 * when *Done for now* is pressed, not when the picker next opens — those are exits, and there
 * are several, and a rule spread over several exits is a rule that gets a new exit added
 * without it. Being in the app is the *definition*, so this is one call on the entry gate's app
 * branch.
 *
 * Before it existed, nothing declared that a walk had ended. A player who rated two sports,
 * entered the app and then resumed an unfinished run was still inside the first walk as far as
 * the app was concerned, and read "Rating 2 of 2" for a single run.
 *
 * **Ending is done before the app is drawn** — a layout effect, not a passive one. Nothing reads a
 * pass once the player is in the app, so for ending alone a passive effect was soon enough; landing
 * is what is not (below). Beginning is done elsewhere for its own reason — the question screen
 * reads a position on its first render.
 *
 * ## The ended pass is read once, for where it began
 *
 * A pass has an origin, and where it ends is read off it
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3, amended by [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §5): a pass begun at the Skill passport's *Add a sport* ends **on the passport**, and the
 * passport is a screen inside the app. Every way out of that pass — *See your ratings*, the
 * leave sheet's *continue later*, its *abandon* — enters the app at `/`, as every pass does,
 * and it is this branch, on ending the pass, that lands it: the origin is handed to
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
 * **A pass begun at Home lands nowhere further**: `/` is Home, which is where it began.
 *
 * ## A landing is made before the app draws anything
 *
 * Every way out arrives at `/`, and `/` is Home. A landing made after the app had drawn showed
 * Home for a frame and then slid the group in over it — a blink, seen on a device. So the hook
 * **says whether a landing is due**, read once from the pass as the gate mounts, and the gate
 * draws nothing until it has been made: the landing is made in the layout effect, before the first
 * frame, and the caller's landing lays its whole stack in one reset (`shell`'s `useShellLanding`).
 * The gate is mounted afresh for every pass that comes back to it, because the questions are a
 * sibling of the app rather than inside it — so a pass begun from inside the app, as a group's
 * door begins one, is never mistaken for one arriving.
 *
 * ## A level got is told to the app as the pass ends
 *
 * A new level changes reads that are not this feature's: Home's ASKED FOR A LEVEL card for the sport
 * ends the moment it is got, and the bell's *level asked* row with it (#765). This feature cannot
 * name those reads, and **every level is got inside a pass, and every pass ends here** — on the way
 * back from *Your rating*, by whichever door it was begun — so the gate is told the sports the
 * ended pass rated (`onRated`), in the same layout effect, before the shell is drawn: what it drops
 * from a cache is already gone from the app's first frame.
 */

import { useLayoutEffect, useRef, useState } from 'react';

import type { Sport } from '@/shared/vocabulary/sport';

import { returnOf, type PassReturn } from '../domain/onboardingPass';
import { useOnboardingPass } from '../store/onboardingPass.store';

/**
 * What the app does with a pass that has just ended, told where to put it back (`returnOf`):
 * the passport, or a group on its tab with the sport rated last. Called once per pass, and
 * never for a Home pass, from the gate's app branch **before the shell is drawn** — so a landing
 * lays its stack down in one move at the root rather than navigating a shell that is not there.
 */
export type PassLanding = (back: PassReturn) => void;

/**
 * What the app does once a pass that produced a rating has ended — told the sports it rated, in
 * the order they were. Called once per such pass, before the shell is drawn, whatever its origin.
 */
export type PassRated = (sports: readonly Sport[]) => void;

/**
 * @param inTheApp whether the entry gate has landed the player in the authenticated tree.
 * Passed rather than read here so the gate keeps one answer, and the caller stays a route
 * file that turns a decision into a route.
 * @param land where the app puts a player whose pass just ended, by the pass's origin.
 * @param onRated what the app does with the sports a pass that just ended rated — see above.
 * @returns whether a landing is still due — the gate draws nothing of the app while it is.
 */
export function useEndOnboardingPass(
  inTheApp: boolean,
  land: PassLanding,
  onRated: PassRated,
): boolean {
  const end = useOnboardingPass((state) => state.end);

  // The latest landing, read at the moment of ending rather than closed over: a landing that
  // reads the current path is a new function per render, and an effect keyed on it would
  // re-run on every render of the gate — harmlessly, since a second `end` finds nothing, but
  // the effect's one job is to fire on *arriving*, and its dependencies should say so.
  const landing = useRef(land);
  landing.current = land;
  const rating = useRef(onRated);
  rating.current = onRated;

  // Read once, as the gate mounts: a pass still held then is one coming back from the questions,
  // while a pass begun with the gate up — at a group's door — is one leaving, and lands nothing.
  const [landingDue, setLandingDue] = useState(() => {
    const pass = useOnboardingPass.getState().pass;
    return pass !== undefined && returnOf(pass) !== undefined;
  });

  useLayoutEffect(() => {
    if (!inTheApp) return;
    const ended = end();
    if (ended !== undefined && ended.rated.length > 0) {
      rating.current(ended.rated.map((run) => run.sport));
    }
    const back = ended === undefined ? undefined : returnOf(ended);
    if (back !== undefined) landing.current(back);
    setLandingDue(false);
  }, [inTheApp, end]);

  return landingDue;
}
