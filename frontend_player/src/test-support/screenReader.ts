/**
 * **A screen reader running, for one test** — and put back afterwards.
 *
 * React Native's jest preset already mocks `AccessibilityInfo.isScreenReaderEnabled` with a
 * `jest.fn` answering `false`, so `jest.spyOn` hands that same mock back rather than wrapping it,
 * and `restoreAllMocks` cannot undo an answer set on it. Left alone, `true` outlives the test, and
 * every later test in the file that awaits anything hears a screen reader — which collapses every
 * presentation it draws. `stopHearingAScreenReader` in an `afterEach` gives the mock its own answer
 * back.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { AccessibilityInfo } from 'react-native';

/** The OS answers that a screen reader is running. Let the promise land before asserting. */
export function hearAScreenReader(): void {
  jest.spyOn(AccessibilityInfo, 'isScreenReaderEnabled').mockResolvedValue(true);
}

/** The preset's own answer back: no screen reader. */
export function stopHearingAScreenReader(): void {
  jest.spyOn(AccessibilityInfo, 'isScreenReaderEnabled').mockResolvedValue(false);
}
