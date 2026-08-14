/**
 * The runs that produced a rating in this pass through onboarding.
 *
 * ## Why the list cannot be derived
 *
 * The done screen shows *what this run produced*, which is not the same question as *what
 * this player is rated at*. A player who resumed an unfinished tennis run already holds a
 * padel rating; listing the ratings collection would put padel on a screen that says these
 * are the ratings you just produced, and the player never answered a padel question today.
 *
 * Nothing on the server records a "run" in that sense either — an assessment is per sport,
 * and the sequence of them is a decision the player made on the picker. So the sequence is
 * held here, where the rest of that decision already lives.
 *
 * ## What it holds, and what it must never hold
 *
 * **Identifiers only.** Which assessment, and which sport. Every number a rating is made
 * of — the Level, the range, the Confidence, the status — belongs to TanStack Query, and a
 * copy here would be a second answer to what this player was rated at, one of which would
 * be stale (docs/architecture.md Part 8).
 *
 * ## Why it is not persisted
 *
 * Same reason as the sport queue: it describes a walk through a flow, not a fact about a
 * player. The run ends when the player enters the app, and a rating outlives it on the
 * server, which is where a player reads it back from afterwards.
 */

import { create } from 'zustand';

import type { Sport } from '../domain/Sport';

export interface CompletedRun {
  readonly assessmentId: string;
  readonly sport: Sport;
}

interface CompletedRunsState {
  /** In the order the ratings were produced, which is the order they were rated in. */
  readonly completed: readonly CompletedRun[];
  readonly record: (run: CompletedRun) => void;
  readonly reset: () => void;
}

export const useCompletedRuns = create<CompletedRunsState>((set) => ({
  completed: [],
  // Recording the same run twice is a no-op rather than a second card: the result screen
  // records what it is showing, and it shows it again on every refetch and remount.
  record: (run) =>
    set((state) =>
      state.completed.some((done) => done.assessmentId === run.assessmentId)
        ? state
        : { completed: [...state.completed, run] },
    ),
  reset: () => set({ completed: [] }),
}));
