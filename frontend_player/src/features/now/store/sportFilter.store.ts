/**
 * The sport bar's selection — ephemeral UI state, feature-scoped, and the only
 * store this feature has.
 *
 * It is not server data and it is not a fact about the player: `ADR-0084` is
 * explicit that *"the selection is never a server-side fact"* — it rides on the
 * request and nothing else, because a tap on a filter chip is not a statement
 * about who somebody is, and storing it would let a stray tap follow her to a new
 * phone. So it is not persisted to the device either.
 *
 * **The rules live in `domain/visit`**, so they are testable without a store and
 * without a renderer. This holds the value and the moment she left.
 *
 * `leftAt` is written when the app **backgrounds**, not when a selection is made,
 * because the rule is measured in time *away*: half an hour on a train with the
 * app open is not half an hour away from it.
 */

import { create } from 'zustand';

import { withinSameVisit } from '../domain/visit';
import { DEFAULT_SPORT_FILTER } from '../mappers/sportBar';
import type { SportFilter } from '../mappers/codes';

interface SportFilterState {
  readonly selected: SportFilter;
  /** When the app last went to the background. Undefined until it has. */
  readonly leftAt: number | undefined;
  readonly select: (sport: SportFilter) => void;
  /** The app went to the background. Starts the clock the visit rule reads. */
  readonly left: (now: number) => void;
  /**
   * The app came back. Keeps the selection inside a visit and resets it outside
   * one — never the other way round, because the harm is one-sided: a remembered
   * filter can hide a match she has paid for.
   */
  readonly returned: (now: number) => void;
  readonly reset: () => void;
}

export const useSportFilterStore = create<SportFilterState>((set, get) => ({
  selected: DEFAULT_SPORT_FILTER,
  leftAt: undefined,
  select: (sport) => set({ selected: sport }),
  left: (now) => set({ leftAt: now }),
  returned: (now) => {
    if (withinSameVisit(get().leftAt, now)) return;
    set({ selected: DEFAULT_SPORT_FILTER, leftAt: undefined });
  },
  reset: () => set({ selected: DEFAULT_SPORT_FILTER, leftAt: undefined }),
}));
