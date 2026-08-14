/**
 * Runs the player asked to come back to later — **this app session only**.
 *
 * ## Why this exists at all
 *
 * "Continue later" changes nothing on the server: the run stays in progress, with every
 * answer intact, which is the whole point of it. But the entry gate routes an unfinished
 * run straight back to its outstanding question — so without something holding the
 * player's *decision*, tapping "continue later" would put them back on the question they
 * just left, one frame later. The way out would not be a way out.
 *
 * So the decision is held here, and the gate reads it. The server state and the routing
 * state are genuinely different facts, and this is the second one.
 *
 * ## Why it is not persisted, and why that is the feature
 *
 * The acceptance criterion is that **relaunching returns to the outstanding question**.
 * An in-memory store gives exactly that for free: the deferral dies with the process, so
 * the next launch resumes. Persisting it would quietly turn "continue later" into
 * "abandon without discarding" — a third state nobody asked for, and one that would trap
 * a run in limbo with no control to get it back.
 *
 * Abandonment is the *permanent* way out and it is a server-side transition. This is the
 * temporary one, and it is not a fact about the player's rating, so it never leaves the
 * device.
 *
 * ## Why this is not part of the onboarding pass
 *
 * It looks like it should be — it is in-memory routing state about onboarding, which is
 * what a pass holds — and it must not be. **The two have different lifetimes.** A pass
 * ends when the player reaches the app; a deferral's whole job is to survive that, because
 * the entry gate is evaluated again the moment they get there. Folded into the pass, a
 * deferral would be cleared at exactly the instant the gate next reads it, and the player
 * who tapped "continue later" would be sent straight back into the run they set aside —
 * which is the bug this store exists to prevent, reintroduced by a tidier structure.
 */

import { create } from 'zustand';

interface DeferredRunsState {
  /** Assessment ids the player has set aside since launch. */
  readonly deferred: readonly string[];
  readonly defer: (assessmentId: string) => void;
  readonly reset: () => void;
}

export const useDeferredRuns = create<DeferredRunsState>((set) => ({
  deferred: [],
  defer: (assessmentId) =>
    set((state) =>
      state.deferred.includes(assessmentId)
        ? state
        : { deferred: [...state.deferred, assessmentId] },
    ),
  reset: () => set({ deferred: [] }),
}));
