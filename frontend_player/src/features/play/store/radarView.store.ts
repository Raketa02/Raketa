/**
 * Where the radar was left: the view — position and zoom — and who is selected. **Kept while
 * the app lives**, across the Deck | Radar toggle and across tabs; a cold start opens at home
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §7, [`the-radar.md`](../../../../../docs/specs/matchmaking/the-radar.md) §7.6).
 *
 * ## The process's lifetime, which is `playPreferences`' and not `playSession`'s
 *
 * The shell keeps no per-tab history and Players opens on Deck every time (ADR-0169 §1), so the
 * pane's own `useState` dies with every tab press — which is exactly the moment the spec wants
 * the view to survive. `playSession` is cleared when the shell lays a stack down, so it is the
 * wrong lifetime too. This store lives for the process, as `playPreferences` does, and for the
 * same reason that store gives: a relaunch landing at home is correct behaviour, not a lost
 * preference. Nothing writes across the three stores.
 *
 * ## In kilometres, never in points
 *
 * The view is `domain/radarGeometry`'s `RadarView` — the kilometre point at the focus and the
 * width in kilometres — so what is kept is *where the player was looking* and not where a tile
 * sat on one phone's field. `undefined` is **home**, which is the state the radar opens in and
 * the state ◉ returns to; it is not a view of its own because home depends on the reach, which
 * the pane reads off the profile and this store never learns.
 *
 * ## The selection is kept by sport, so a sport switch clears it by construction
 *
 * *A sport switch clears the selection and keeps position and zoom* (§7.5). The selection is
 * held with the sport it was made in, and the pane reads it only for the sport it is on — so a
 * chip press on the deck pane, out of the radar's sight, clears it too, and no effect has to
 * watch the sport to do it. What the store holds is an id and a sport; the row it names is the
 * reading's, and *a selected player absent from the next reading is deselected silently* is
 * `domain/reading`'s `selectionOn`, applied at read.
 *
 * Nothing from the backend enters this store: the reading is TanStack Query's, and the id here
 * is a pointer into it, never a copy of the row.
 */

import { create } from 'zustand';

import type { Sport } from '@/shared/vocabulary/sport';

import type { RadarView } from '../domain/radarGeometry';

/** Who is selected, and in which sport's reading. */
export interface RadarSelection {
  readonly sport: Sport;
  readonly playerId: string;
}

interface RadarViewState {
  /** Where the radar is looking, or `undefined` for home. */
  readonly view: RadarView | undefined;
  readonly selection: RadarSelection | undefined;
  /** A gesture, a ±, or a flight has ended somewhere. */
  readonly setView: (view: RadarView) => void;
  /** A tap on a face — after the flight, or at once under reduced motion. */
  readonly select: (selection: RadarSelection) => void;
  /** A tap on the field. The view stays. */
  readonly deselect: () => void;
  /** ◉ — home, deselected. */
  readonly goHome: () => void;
  /** Back to nothing kept. What a suite uses to stand in for process death. */
  readonly reset: () => void;
}

export const useRadarView = create<RadarViewState>((set) => ({
  view: undefined,
  selection: undefined,
  setView: (view) => set({ view }),
  select: (selection) => set({ selection }),
  deselect: () => set({ selection: undefined }),
  goHome: () => set({ view: undefined, selection: undefined }),
  reset: () => set({ view: undefined, selection: undefined }),
}));

/** The selected player, for the sport the pane is on — nobody, when the selection was made in another. */
export function selectedIn(
  selection: RadarSelection | undefined,
  sport: Sport | undefined,
): string | undefined {
  return selection !== undefined && selection.sport === sport ? selection.playerId : undefined;
}
