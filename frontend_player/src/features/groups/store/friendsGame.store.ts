/**
 * **The game being built on a group's Friends tab** — its kind, and who is seated where
 * ([#757](https://github.com/Rakieta02/Rakieta/issues/757); the friends mechanics §7.1–§7.3).
 *
 * **The kind is this game's, and nothing else's** (ADR-0202; the friends README's defaults: *the
 * Friends tab's kind switch is per game, never intent*). Until #757 the switch shared
 * `gameIntent.store` with the Games deck and *Post a game*, so turning it moved the deck. It is its
 * own value now, and keeps its position while the app is open, in memory only, as ADR-0188 §5
 * keeps it — one value for the app, not one per group, because a player building a game does not
 * change their mind by opening another group. **It is picked in the Friends tab's menu** since #861
 * (PRD #859) — the page's `TabMenu`, where a switch above the court stood.
 *
 * **The line-up is the page's**, one per group and sport — the court a sport is drawn for has its
 * own number of seats. It is a store rather than the tab's state because **the picker is pushed over
 * the page** and seats its picks on Done, from another screen; and it goes when the page does, as
 * *Post a game*'s draft goes (`GroupScreen`), so the page opens on an empty court the next time.
 * Nothing from the backend is here: the line-up is choices, and the card is TanStack Query's.
 */

import { create } from 'zustand';

import type { Sport } from '@/shared/vocabulary/sport';

import type { FriendsLineUp } from '../domain/friendsLineUp';
import type { GameIntent } from '../domain/groupPage';

/** One line-up per group and sport. */
export function lineUpKey(groupId: string, sport: Sport): string {
  return `${groupId}/${sport}`;
}

interface FriendsGameState {
  readonly kind: GameIntent;
  readonly lineUps: Readonly<Record<string, FriendsLineUp>>;
  readonly choose: (kind: GameIntent) => void;
  readonly put: (groupId: string, sport: Sport, lineUp: FriendsLineUp) => void;
  /** The page went: every sport's line-up of the group goes with it. The kind stays. */
  readonly forget: (groupId: string) => void;
}

export const useFriendsGame = create<FriendsGameState>((set) => ({
  kind: 'competitive',
  lineUps: {},
  choose: (kind) => set({ kind }),
  put: (groupId, sport, lineUp) =>
    set((state) => ({ lineUps: { ...state.lineUps, [lineUpKey(groupId, sport)]: lineUp } })),
  forget: (groupId) =>
    set((state) => {
      const kept = Object.entries(state.lineUps).filter(([key]) => !key.startsWith(`${groupId}/`));
      if (kept.length === Object.keys(state.lineUps).length) return state;
      return { lineUps: Object.fromEntries(kept) };
    }),
}));
