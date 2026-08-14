/**
 * The sport queue — the one piece of onboarding state that is neither server data nor
 * local to a component.
 *
 * It is wizard progress: chosen on the picker, read by every screen after it, and gone
 * when the run is. **It is never written to the server and never persisted to the
 * device** — it only orders the next few assessments, and a sport not rated today can be
 * rated any time later.
 *
 * Nothing from the backend enters this store. Ratings and assessments are TanStack
 * Query's, and a second copy here would be a second answer to "what has this player
 * been rated at".
 */

import { create } from 'zustand';

import type { Sport } from '../domain/Sport';
import { toggleSport } from '../domain/sportQueue';

interface SportQueueState {
  /** The sports chosen, in the order they were chosen. */
  readonly queue: readonly Sport[];
  readonly toggle: (sport: Sport) => void;
  readonly reset: () => void;
}

export const useSportQueue = create<SportQueueState>((set) => ({
  queue: [],
  // The rule lives in `domain/sportQueue`, so it is testable without a store and
  // without a renderer. The store only holds the result.
  toggle: (sport) => set((state) => ({ queue: toggleSport(state.queue, sport) })),
  reset: () => set({ queue: [] }),
}));
