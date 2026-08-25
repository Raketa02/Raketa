/**
 * The profile draft, while the player is inside onboarding's second part.
 *
 * In memory, never persisted, and **never sent anywhere until the commit** — which is what
 * makes it the part's checkpoint rather than a cache of one
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)). Killing
 * the app takes the draft with it, and the next launch starts the part again at step one
 * with nothing in it. That is the accepted cost of not building a server-owned draft, and
 * it is bounded by six short steps.
 *
 * **The rules live in `domain/ProfileDraft`**, so they are testable without a store and
 * without a renderer. This holds the value and nothing else — the same split the onboarding
 * pass uses.
 *
 * ## Absent is a state, and it is the load-bearing one
 *
 * `draft` is `undefined` when the player is not in the part, exactly as `pass` is undefined
 * between walks. That absence is what a step other than the first checks: a link naming
 * `/radius` with no part running is not a shortcut into the middle of a flow, it is a
 * player about to commit a profile built from five screens they never saw. Turning them
 * away needs a way to tell *not in the part* from *in the part, having answered nothing* —
 * and an empty draft cannot tell those apart, which is why entering is explicit.
 *
 * Nothing from the backend enters this store. The served tag vocabulary and radius bounds
 * are TanStack Query's; what is here is only what the player has said.
 */

import { create } from 'zustand';

import { emptyDraft, recordAnswer, type ProfileDraft } from '../domain/ProfileDraft';

interface ProfileDraftState {
  /** Undefined outside the part. See above — absence is the state that makes this work. */
  readonly draft: ProfileDraft | undefined;
  /**
   * Enter the part, **only if it is not already running**.
   *
   * Called by the first step, which is the only door in: the entry gate redirects there
   * and every other step turns a stranger away to it. Conditional because walking *back*
   * to step one is an ordinary move, and beginning again there would wipe the five answers
   * the player walked back past.
   */
  readonly enterIfAbsent: () => void;
  /** Record what one step answered. A no-op outside the part — there is nothing to write to. */
  readonly answer: (answer: Partial<ProfileDraft>) => void;
  /**
   * Back to no part running.
   *
   * The part's only ending today is process death, which clears an in-memory store without
   * anybody asking it to — so this exists for the suites that need a clean one. The *other*
   * ending, the commit, arrives with its own ticket and brings the call site that means it.
   */
  readonly reset: () => void;
}

export const useProfileDraft = create<ProfileDraftState>((set, get) => ({
  draft: undefined,
  enterIfAbsent: () => {
    if (get().draft !== undefined) return;
    set({ draft: emptyDraft() });
  },
  // Dropped rather than starting a part, for the reason the pass drops a rating recorded
  // with no pass running: every screen that can answer was reached through the one that
  // enters, so this guards against a future caller rather than a case the flow produces.
  answer: (answer) =>
    set((state) =>
      state.draft === undefined ? state : { draft: recordAnswer(state.draft, answer) },
    ),
  reset: () => set({ draft: undefined }),
}));
