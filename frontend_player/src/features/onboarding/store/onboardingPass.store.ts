/**
 * The onboarding pass — the one piece of onboarding state that is neither server data nor
 * local to a component.
 *
 * It is wizard progress: begun when a walk through the questionnaire starts — at a door
 * where play begins, an official group's card, or the Skill passport's *Add a sport* — read by
 * every screen in it, and **gone when the player reaches the app**. It is never written to the
 * server and never persisted to the device — it only orders the next few assessments and
 * accounts for what they produced, and a sport not rated today can be rated any time later
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §5). **A pass
 * carries its origin**, and the origin is the rule for where it ends: the entry gate ends every
 * pass on reaching the app, and lands it back where it began.
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
 * **There are no deferred runs any more.** A run set aside with *continue later* was held in a
 * store of its own, so the gate's *resume* would not send the player straight back into it; the
 * gate resumes nothing now (ADR-0200 §5), and the door's *Carry on* is the only way back in.
 */

import { create } from 'zustand';

import type { Sport } from '@/shared/vocabulary/sport';
import {
  FROM_HOME,
  begin as beginPass,
  recordRated,
  type DoorOrigin,
  type OnboardingPass,
  type PassOrigin,
  type RatedRun,
} from '../domain/onboardingPass';

interface OnboardingPassState {
  /** Undefined between walks. See above — absence is the state that makes this work. */
  readonly pass: OnboardingPass | undefined;
  /**
   * Start a pass over these sports, at the door it came in by: the picker's continue with
   * what was chosen, or a chip, a group's card or the door's *Carry on* with its one sport.
   */
  readonly begin: (queue: readonly Sport[], origin: PassOrigin) => void;
  /**
   * **The picker turned back from, before anything was chosen** — a pass over no sport, begun and
   * over at once, so the gate lands it where it began: the one way back the gate already knows.
   */
  readonly turnBack: (origin: DoorOrigin) => void;
  /**
   * Start a pass over these sports **only if none is running**.
   *
   * The question route's, for a run reached with no pass running — a link, since every door
   * begins one: that is a genuine pass of one sport, and saying so is what lets the position
   * rule stop special-casing it. Its origin is Home, the app's root, which is where it ends.
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
  turnBack: (origin) => set({ pass: beginPass([], origin) }),
  beginIfAbsent: (queue) => {
    if (get().pass !== undefined) return;
    set({ pass: beginPass(queue, FROM_HOME) });
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
