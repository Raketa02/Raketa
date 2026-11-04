/**
 * The onboarding pass — the one piece of onboarding state that is neither server data nor
 * local to a component.
 *
 * It is wizard progress: begun when a walk through onboarding starts — at the picker, or
 * at the Skill passport's *Add a sport* — read by every screen in it, and **gone when the
 * player reaches the app**. It is never written to the server and never persisted to the
 * device — it only orders the next few assessments and accounts for what they produced, and
 * a sport not rated today can be rated any time later from the passport
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3). **A pass carries its origin**, and the origin is the rule for where it ends: the
 * entry gate ends every pass on reaching the app, and lands a passport-begun one back on
 * the passport.
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

import type { Sport } from '@/shared/vocabulary/sport';
import {
  FROM_WELCOME,
  begin as beginPass,
  recordRated,
  type OnboardingPass,
  type PassOrigin,
  type RatedRun,
} from '../domain/onboardingPass';

interface OnboardingPassState {
  /** Undefined between walks. See above — absence is the state that makes this work. */
  readonly pass: OnboardingPass | undefined;
  /**
   * Start a pass over these sports, at the door it came in by: the picker's continue with
   * what was chosen, or a chip or a group's card with its one sport.
   */
  readonly begin: (queue: readonly Sport[], origin: PassOrigin) => void;
  /**
   * Start a pass over these sports **only if none is running**.
   *
   * The question route's, for a run resumed straight from the entry gate with no picker in
   * between: that is a genuine pass of one sport, and saying so is what lets the position
   * rule stop special-casing it. Its origin is welcome, whichever door the run was first
   * begun at — the gate's *resume* branch keeps its rule, and a run set aside from the
   * passport and resumed on the next launch ends the way any resumed run does (ADR-0179 §3,
   * Consequences).
   */
  readonly beginIfAbsent: (queue: readonly Sport[]) => void;
  /** Record that a run produced a rating. Recording it twice is a no-op. */
  readonly record: (run: RatedRun) => void;
  /**
   * The pass is over. **Hands back the pass it ended**, or nothing when none was running.
   *
   * Called from one site — the entry gate's app branch — which is what makes this the
   * *definition* of a pass ending rather than a line someone must remember on every exit.
   * Ending may be lazy because nothing reads a pass once the player is in the app; what is
   * read is the ended pass's origin, once, by the gate, to land a pass begun on the passport
   * or on a group back where it began. Returned rather than subscribed to, because a gate that re-rendered
   * on every change to the pass would end the one the chip has just begun.
   */
  readonly end: () => OnboardingPass | undefined;
  readonly reset: () => void;
}

export const useOnboardingPass = create<OnboardingPassState>((set, get) => ({
  pass: undefined,
  begin: (queue, origin) => set({ pass: beginPass(queue, origin) }),
  beginIfAbsent: (queue) => {
    if (get().pass !== undefined) return;
    set({ pass: beginPass(queue, FROM_WELCOME) });
  },
  // A rating recorded with no pass running is dropped rather than beginning one. Every
  // route that shows a result was reached through a screen that begins one, so this is
  // a guard against a future caller, not a case the flow produces.
  record: (run) =>
    set((state) => (state.pass === undefined ? state : { pass: recordRated(state.pass, run) })),
  end: () => {
    const ended = get().pass;
    if (ended !== undefined) set({ pass: undefined });
    return ended;
  },
  reset: () => set({ pass: undefined }),
}));
