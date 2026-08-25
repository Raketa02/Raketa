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
 * decision already taken. One latch covers **every** way off a screen in this run — onward
 * through the pass, to this sport's result, to the review the stop leads to, and back into
 * the questionnaire at an answer — because they are alternatives, and a run that finishes
 * while an abandonment is departing must not produce two navigations.
 *
 * **A failed start releases it.** The abandonment that may have preceded it still stands —
 * it is a state transition on the server and there is nothing to undo — so only the
 * departure failed, and the player must be able to try it again.
 *
 * ## The end of the queue is not the end of onboarding
 *
 * Onboarding is two parts, and the second one is where a Player profile is collected. So
 * the last sport does not lead to the closing screens for a player who has not committed
 * one — it leads to the six social steps, and the commit at the end of them leads to the
 * closing screens. That ordering is the spec's, and it is what gives the last social step
 * something to continue to.
 *
 * **Whether a profile exists is the auth feature's answer**, read through the query the gate
 * already asks rather than a second one against the same route. A launch that has not
 * answered it yet reads as *has one*, which is the fail-safe direction: the closing screens
 * lead to the app, the gate there has the last word, and it will turn a player who really is
 * owed the second part straight into it. The other default walks a set-up player through six
 * steps and ends on a commit the server refuses.
 */

import { useRouter } from 'expo-router';
import { useCallback, useRef } from 'react';

import { useCurrentUser } from '@/features/auth/types';
import { SOCIAL_STEPS_ENTRY } from '@/features/player_profile/types';
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
   * sport, and leaving has several destinations.
   */
  readonly showResultOf: (assessmentId: string) => void;
  /**
   * The questionnaire stopped, so the review is next — the last look before the rating
   * exists (ADR-0020).
   *
   * The third destination out of the question loop, and the reason it is here rather than
   * in the screen is the latch: a stopped run, a finished one and an abandonment are
   * alternatives, and a step arriving mid-departure must not navigate on top of a
   * decision already taken.
   */
  readonly showReviewOf: (assessmentId: string) => void;
  /**
   * Back into the questionnaire, standing on a question already answered — what a review
   * entry opens, and where a run that is still asking belongs.
   *
   * `position` omitted means *wherever the run stands*, which is the outstanding question.
   * It is navigation input rather than state: it says where the player starts standing,
   * and every move after it is local to the screen and costs nothing.
   */
  readonly showQuestionAt: (assessmentId: string, position?: number) => void;
  /** A start is in flight. Drives the busy control, and the leave sheet's busy state. */
  readonly advancing: boolean;
  /** The failed start, if the last one failed. Rendered with the usual error note. */
  readonly error: AppError | null;
}

/**
 * The one place a pass destination becomes a route.
 *
 * `rate` is not here: it needs an assessment started before there is anything to navigate
 * to, which is the whole of what `advance` does beyond this table.
 */
function leavesTo(destination: PassDestination): '/done' | typeof SOCIAL_STEPS_ENTRY | '/' {
  switch (destination.kind) {
    case 'closing':
      return '/done';
    case 'social-steps':
      // Where the second part begins is the feature that owns it saying so — the entry gate
      // reaches for the same value, and two files spelling the route was two places to
      // change it.
      return SOCIAL_STEPS_ENTRY;
    default:
      return '/';
  }
}

export function useAdvanceThroughPass(sport: Sport): PassAdvance {
  const router = useRouter();
  const pass = useOnboardingPass((state) => state.pass);
  const player = useCurrentUser();
  const start = useStartAssessment();
  const startNext = start.mutate;

  const departing = useRef(false);

  // See the note above on why *not yet answered* reads as *has one*.
  const hasPlayerProfile = player.data?.hasPlayerProfile ?? true;
  const destination = nextDestination(pass, sport, { hasPlayerProfile });

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

  const showReviewOf = useCallback(
    (assessmentId: string) => {
      if (departing.current) return;
      departing.current = true;
      router.replace({ pathname: '/review/[assessmentId]', params: { assessmentId, sport } });
    },
    [router, sport],
  );

  const showQuestionAt = useCallback(
    (assessmentId: string, position?: number) => {
      if (departing.current) return;
      departing.current = true;
      router.replace({
        pathname: '/question/[assessmentId]',
        params:
          position === undefined ? { assessmentId, sport } : { assessmentId, sport, at: position },
      });
    },
    [router, sport],
  );

  const stopHere = useCallback(() => {
    if (departing.current) return;
    departing.current = true;
    router.replace(leavesTo(stopDestination(pass, { hasPlayerProfile })));
  }, [hasPlayerProfile, pass, router]);

  const advance = useCallback(() => {
    if (departing.current) return;
    departing.current = true;

    if (destination.kind !== 'rate') {
      // The end of the queue, routed by what the pass produced and what the player still
      // owes: setting up when it is not done, the closing screens when it is, and the app
      // when there is nothing to account for. Every one of them is a `replace`.
      router.replace(leavesTo(destination));
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
    showReviewOf,
    showQuestionAt,
    advancing: start.isPending,
    error: start.error,
  };
}
