/**
 * *Add a sport* — the second door into the onboarding pass
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3).
 *
 * The Skill passport draws one chip per unrated sport, and pressing one does exactly what the
 * picker's continue does for its first sport: start the assessment, begin a pass, and land on
 * the opening question. The differences are the two facts the origin carries — the queue is
 * one sport, and the pass ends back on the passport — and both are the pass's, not the chip's.
 * What crosses the feature's public surface is the act, never the store.
 *
 * **The start is the picker's own hook**, so a sport with an unfinished run gets that run back
 * rather than a second one — the server answers the outstanding run for a sport already
 * being rated, exactly as it does when the picker names it.
 *
 * **The pass begins on success, not on press.** The picker begins before it starts, and can:
 * a failed start there leaves the player on the picker, inside onboarding, where a pass lying
 * around costs nothing. Here the player is *in the app*, and between passes there is no pass —
 * that absence is what lets the gate's resume path begin one honestly. A pass begun at the
 * chip and stranded by a failed start would be exactly the value `onboardingPass.store` says
 * must not exist while the player is in the app. So nothing begins until there is a run to
 * begin over, and the begin and the departure are one synchronous step: the question screen
 * reads its position on its first render, and the store is written before the route is.
 *
 * **`replace`, not `push`**, as the picker's is. The passport is a screen inside the app's tree
 * and the questionnaire is a sibling group of it; the way back is the pass ending, which the
 * gate reads off the origin, and the system back gesture must not be a second, unlabelled way
 * out of the run.
 */

import { useRouter } from 'expo-router';
import { useCallback, useRef } from 'react';

import type { AppError } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import { useOnboardingPass } from '../store/onboardingPass.store';

import { useStartAssessment } from './useStartAssessment';

export interface AddASport {
  /** Begin a pass of this one sport, from the passport. */
  readonly rate: (sport: Sport) => void;
  /** The sport whose start is in flight, so its chip alone can say so. */
  readonly starting: Sport | undefined;
  /** The failed start, if the last one failed. The passport draws it beside the chips. */
  readonly error: AppError | null;
}

export function useAddASport(): AddASport {
  const router = useRouter();
  const beginPass = useOnboardingPass((state) => state.begin);
  const start = useStartAssessment();
  const startRun = start.mutate;

  // The latch `useAdvanceThroughPass` keeps, for the same reason: a second chip pressed while
  // the first start is in the air would open a second run for a second sport, and the player
  // would be routed into whichever landed last. A ref rather than the mutation's `isPending`,
  // which is a render behind the press that set it.
  const inFlight = useRef(false);

  const rate = useCallback(
    (sport: Sport) => {
      if (inFlight.current) return;
      inFlight.current = true;
      startRun(sport, {
        onSuccess: (opening) => {
          beginPass([sport], 'passport');
          router.replace({
            pathname: '/question/[assessmentId]',
            params: { assessmentId: opening.assessmentId, sport },
          });
        },
        // Released on failure only: a start that landed is followed by a departure, and this
        // screen is gone. A failed one leaves the chip to be pressed again.
        onError: () => {
          inFlight.current = false;
        },
      });
    },
    [beginPass, router, startRun],
  );

  return {
    rate,
    starting: start.isPending ? start.variables : undefined,
    error: start.error,
  };
}
