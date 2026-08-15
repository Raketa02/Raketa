/**
 * Leaving the flow from inside a run — the confirm, and the two doors it offers.
 *
 * **Two screens can be left this way and they must be left identically.** The question
 * screen has always offered it; the review offers it because a player who has answered
 * everything and rated nothing must be able to walk away without creating a rating
 * ([ADR-0020](../../../../../docs/adr/0020-revisable-assessment-answers.md)). "Identically"
 * is not a promise a second copy can keep — `useAdvanceThroughPass` exists because
 * *start the next sport and go there* was written twice and the two copies had already
 * diverged — so the wiring lives here and the screens render the sheet.
 *
 * - **Continue later** sends nothing. The run stays in progress with every answer intact,
 *   and the gate is told to leave it alone until the next launch, which is what makes this
 *   a way out rather than a redirect back one frame later.
 * - **Stop rating this sport** abandons the run and then takes whatever the pass says
 *   comes next. The confirm stays open until the flow has somewhere to be, so a failure on
 *   either half lands in front of the player beside the control that retries it.
 *
 * **The advance is passed in rather than taken here**, because it carries the departure
 * latch: a second instance would be a second latch, and two latches cannot stop each other
 * navigating.
 */

import { useRouter } from 'expo-router';
import { useCallback, useRef, useState, type MutableRefObject } from 'react';
import type { View } from 'react-native';

import type { AppError } from '@/shared/errors';

import { useDeferredRuns } from '../store/deferredRuns.store';

import { useAbandonAssessment } from './useAbandonAssessment';
import type { PassAdvance } from './useAdvanceThroughPass';

export interface LeaveAssessment {
  /** The confirm is open. */
  readonly confirming: boolean;
  /** Open it — what the header's close control does. */
  readonly ask: () => void;
  /** Dismissal: the scrim, the sheet's close control, the Android back gesture, a button. */
  readonly keepGoing: () => void;
  readonly continueLater: () => void;
  readonly stopRating: () => void;
  /** The abandonment, or the next sport's opening question: one departure to the player. */
  readonly leaving: boolean;
  readonly error: AppError | null;
  /**
   * The control the sheet returns focus to, which is the one that opened it — so the
   * screen attaches this to its close control and hands the same ref to the sheet.
   *
   * Mutable rather than the `FocusTarget` the sheet declares: a target is only *read* by an
   * overlay, but this end of it is written by React attaching a host element, and a
   * read-only ref will not go on a `ref` prop. It widens to `FocusTarget` on the way in.
   */
  readonly returnFocusTo: MutableRefObject<View | null>;
}

export function useLeaveAssessment(assessmentId: string, onwards: PassAdvance): LeaveAssessment {
  const router = useRouter();
  const abandon = useAbandonAssessment(assessmentId);
  const defer = useDeferredRuns((state) => state.defer);

  const [confirming, setConfirming] = useState(false);
  const closeControl = useRef<View | null>(null);

  const { advance, advancing } = onwards;
  const abandonRun = abandon.mutate;

  const continueLater = useCallback(() => {
    setConfirming(false);
    defer(assessmentId);
    router.replace('/');
  }, [assessmentId, defer, router]);

  const stopRating = useCallback(() => {
    // Pressing again re-abandons, which the server treats as a no-op, and tries the
    // departure again.
    abandonRun(undefined, { onSuccess: advance });
  }, [abandonRun, advance]);

  return {
    confirming,
    ask: useCallback(() => setConfirming(true), []),
    keepGoing: useCallback(() => setConfirming(false), []),
    continueLater,
    stopRating,
    leaving: abandon.isPending || advancing,
    error: abandon.error ?? onwards.error,
    returnFocusTo: closeControl,
  };
}
