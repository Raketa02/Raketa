/**
 * The onboarding pass — the one piece of onboarding state that is neither server data nor
 * local to a component.
 *
 * It is wizard progress: begun when a walk through onboarding starts, read by every screen
 * in it, and **gone when the player reaches the app**. It is never written to the server
 * and never persisted to the device — it only orders the next few assessments and accounts
 * for what they produced, and a sport not rated today can be rated any time later.
 *
 * Nothing from the backend enters this store. Ratings and assessments are TanStack
 * Query's, and a second copy here would be a second answer to "what has this player been
 * rated at".
 *
 * **The rules live in `domain/onboardingPass`**, so they are testable without a store and
 * without a renderer. This holds the value and nothing else.
 *
 * ## Absent is a state, and it is the load-bearing one
 *
 * `pass` is `undefined` between walks, and that is what makes `beginIfAbsent` safe. While
 * nothing ended a pass, "no pass" and "a pass nobody cleared" were the same value, so a
 * begin-if-absent would have adopted a finished walk's queue and reported a resumed run as
 * "Rating 2 of 2". Ending reliably is the prerequisite for beginning conditionally; the
 * two arrived together for that reason and neither is safe alone.
 *
 * The picker's selection is **not** here. A player still choosing has not begun anything,
 * and modelling their half-built list as a pass is what made the two states
 * indistinguishable in the first place. It is component state on the picker, ordered by
 * `toggleSport`.
 *
 * Deferred runs are **not** here either, and `store/deferredRuns.store` says why: a
 * deferral outlives a pass, and folding it in would clear one at the moment the entry gate
 * next evaluates.
 */

import { create } from 'zustand';

import type { Sport } from '../domain/Sport';
import {
  begin as beginPass,
  recordRated,
  type OnboardingPass,
  type RatedRun,
} from '../domain/onboardingPass';

interface OnboardingPassState {
  /** Undefined between walks. See above — absence is the state that makes this work. */
  readonly pass: OnboardingPass | undefined;
  /** Start a pass over these sports. The picker's continue, with what was chosen. */
  readonly begin: (queue: readonly Sport[]) => void;
  /**
   * Start a pass over these sports **only if none is running**.
   *
   * The question route's, for a run resumed straight from the entry gate with no picker in
   * between: that is a genuine pass of one sport, and saying so is what lets the position
   * rule stop special-casing it.
   */
  readonly beginIfAbsent: (queue: readonly Sport[]) => void;
  /** Record that a run produced a rating. Recording it twice is a no-op. */
  readonly record: (run: RatedRun) => void;
  /**
   * The pass is over.
   *
   * Called from one site — the entry gate's app branch — which is what makes this the
   * *definition* of a pass ending rather than a line someone must remember on every exit.
   * Ending may be lazy because nothing reads a pass once the player is in the app.
   */
  readonly end: () => void;
  readonly reset: () => void;
}

export const useOnboardingPass = create<OnboardingPassState>((set, get) => ({
  pass: undefined,
  begin: (queue) => set({ pass: beginPass(queue) }),
  beginIfAbsent: (queue) => {
    if (get().pass !== undefined) return;
    set({ pass: beginPass(queue) });
  },
  // A rating recorded with no pass running is dropped rather than beginning one. Every
  // route that shows a result was reached through a screen that begins one, so this is
  // a guard against a future caller, not a case the flow produces.
  record: (run) =>
    set((state) => (state.pass === undefined ? state : { pass: recordRated(state.pass, run) })),
  end: () => set({ pass: undefined }),
  reset: () => set({ pass: undefined }),
}));
