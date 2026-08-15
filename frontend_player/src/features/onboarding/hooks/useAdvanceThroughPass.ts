/**
 * Leaving one sport, wherever the pass says that leads.
 *
 * "Start the next sport and go there" was written twice — once in the question screen and
 * once in the result screen — and the two copies had already diverged. The question
 * screen guarded its departure with a one-way latch and released it when starting the next
 * assessment failed, leaving the failure beside the control that retries it. The result
 * screen had neither, so a failed tap there did nothing visible at all.
 *
 * This owns the whole transition: resolving the destination from the pass, starting the
 * next assessment, navigating, the departure latch, and what happens when the start fails.
 * Both screens then have one call and no navigation logic of their own.
 *
 * **Only the decision crosses the feature's public surface.** `nextDestination` is a pure
 * rule with its own tests; this is the wiring that acts on it, and it stays internal. That
 * is the same split the entry gate already uses — a pure rule, a hook that wires it, and
 * only the decision leaving the feature.
 *
 * ## The latch, and why it is here
 *
 * Every exit is a `replace` and the screen stays mounted while the next one is being
 * arranged, so a step arriving mid-departure could navigate a second time on top of a
 * decision already taken. One latch covers **both** ways out of a sport — onward through
 * the pass, and to this sport's own result — because they are alternatives, and a run that
 * finishes while an abandonment is departing must not produce two navigations.
 *
 * **A failed start releases it.** The abandonment that may have preceded it still stands —
 * it is a state transition on the server and there is nothing to undo — so only the
 * departure failed, and the player must be able to try it again.
 */

import { useRouter } from 'expo-router';
import { useCallback, useRef } from 'react';

import type { AppError } from '@/shared/errors';

import type { Sport } from '../domain/Sport';
import { nextDestination, stopDestination, type PassDestination } from '../domain/onboardingPass';
import { useOnboardingPass } from '../store/onboardingPass.store';

import { useStartAssessment } from './useStartAssessment';

export interface PassAdvance {
  /**
   * Where this sport leads: the next one chosen, the closing screens, or the app.
   *
   * Exposed because a screen has to *label* the control — "Rate Tennis" needs the sport —
   * never so that a screen can decide differently.
   */
  readonly destination: PassDestination;
  /** Take it. A second call while a departure is in flight does nothing. */
  readonly advance: () => void;
  /**
   * Stop before the end of the queue — *done for now*, with sports still to go.
   *
   * Not an abandonment: nothing is discarded and nothing is sent. The sports never rated
   * stay unrated and can be rated any other day. Where it leads is `stopDestination`'s
   * answer, the same one `advance` reaches at the end of the queue.
   */
  readonly stopHere: () => void;
  /**
   * The questionnaire's other way out: this run finished, so its result is next.
   *
   * Here rather than in the question screen because it shares the latch — see above. The
   * result screen has no use for it, which is the honest shape: one hook owns leaving a
   * sport, and leaving has two destinations.
   */
  readonly showResultOf: (assessmentId: string) => void;
  /** A start is in flight. Drives the busy control, and the leave sheet's busy state. */
  readonly advancing: boolean;
  /** The failed start, if the last one failed. Rendered with the usual error note. */
  readonly error: AppError | null;
}

export function useAdvanceThroughPass(sport: Sport): PassAdvance {
  const router = useRouter();
  const pass = useOnboardingPass((state) => state.pass);
  const start = useStartAssessment();
  const startNext = start.mutate;

  const departing = useRef(false);

  const destination = nextDestination(pass, sport);

  const showResultOf = useCallback(
    (assessmentId: string) => {
      if (departing.current) return;
      departing.current = true;
      // `replace`, because this is the exit from the loop, not a step inside it. Moving
      // between questions is state on one route (ADR-0020); leaving the run is a route
      // change, and a player who has been rated must not land back in the questionnaire
      // on the system back gesture.
      router.replace({ pathname: '/result/[assessmentId]', params: { assessmentId, sport } });
    },
    [router, sport],
  );

  const stopHere = useCallback(() => {
    if (departing.current) return;
    departing.current = true;
    router.replace(stopDestination(pass).kind === 'closing' ? '/done' : '/');
  }, [pass, router]);

  const advance = useCallback(() => {
    if (departing.current) return;
    departing.current = true;

    if (destination.kind !== 'rate') {
      // The end of the queue, routed by what the pass produced: the closing screens when
      // something was rated, the app when nothing was. Both are a `replace`.
      router.replace(destination.kind === 'closing' ? '/done' : '/');
      return;
    }

    const next = destination.sport;
    startNext(next, {
      onSuccess: (opening) =>
        router.replace({
          pathname: '/question/[assessmentId]',
          params: { assessmentId: opening.assessmentId, sport: next },
        }),
      onError: () => {
        departing.current = false;
      },
    });
  }, [destination, router, startNext]);

  return {
    destination,
    advance,
    stopHere,
    showResultOf,
    advancing: start.isPending,
    error: start.error,
  };
}
