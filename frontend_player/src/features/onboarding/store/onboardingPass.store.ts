/**
 * The onboarding pass — the one piece of onboarding state that is neither server data nor
 * local to a component.
 *
 * It is wizard progress: chosen on the picker, read by every screen after it, and gone
 * when the pass is. **It is never written to the server and never persisted to the
 * device** — it only orders the next few assessments and accounts for what they produced,
 * and a sport not rated today can be rated any time later.
 *
 * Nothing from the backend enters this store. Ratings and assessments are TanStack
 * Query's, and a second copy here would be a second answer to "what has this player been
 * rated at".
 *
 * **The rules live in `domain/onboardingPass`**, so they are testable without a store and
 * without a renderer. This holds the value and nothing else.
 *
 * Deferred runs are **not** here, and `store/deferredRuns.store` says why: a deferral
 * outlives a pass, and folding it in would clear one at the moment the entry gate next
 * evaluates.
 */

import { create } from 'zustand';

import type { Sport } from '../domain/Sport';
import {
  begin as beginPass,
  recordRated,
  toggleSport,
  type OnboardingPass,
  type RatedRun,
} from '../domain/onboardingPass';

interface OnboardingPassState {
  readonly pass: OnboardingPass;
  /** The picker's selection: add or remove a sport from the queue. */
  readonly choose: (sport: Sport) => void;
  /** Start a fresh pass over these sports, discarding what an earlier one produced. */
  readonly begin: (queue: readonly Sport[]) => void;
  /** Record that a run produced a rating. Recording it twice is a no-op. */
  readonly record: (run: RatedRun) => void;
  readonly reset: () => void;
}

export const useOnboardingPass = create<OnboardingPassState>((set) => ({
  pass: beginPass([]),
  choose: (sport) => set((state) => ({ pass: toggleSport(state.pass, sport) })),
  begin: (queue) => set({ pass: beginPass(queue) }),
  record: (run) => set((state) => ({ pass: recordRated(state.pass, run) })),
  reset: () => set({ pass: beginPass([]) }),
}));
