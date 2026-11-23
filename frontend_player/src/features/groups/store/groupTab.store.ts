/**
 * **Which tab a group's page is on** — held for as long as the page is up, and dropped with it
 * ([#558](https://github.com/Raketa02/Raketa/issues/558)).
 *
 * It was the page's own state, and one screen pushed over the page now has to move it: ***Post a
 * game*** lands the player on **You’re in** — after a post, and by every way back — whether the
 * screen was opened from You’re in's button or from the Games tab. So the screen sets the page's tab
 * to You’re in **when it opens** — under it, unseen — and the chevron, the hardware back and the
 * swipe all arrive there (#847's interim: it was Fill in, which held the yeses, until the split).
 * Any of the four tabs is an entry (`GROUP_TABS`).
 *
 * **The page still always opens on Games** (story 51; ADR-0188 §5 keeps no tab): it forgets its
 * entry when it goes, so the next time it is opened there is nothing to restore. One entry per
 * group, process-scoped, never on the phone.
 */

import { create } from 'zustand';

import type { GroupTab } from '../domain/groupPage';

interface GroupTabState {
  readonly tabs: Readonly<Record<string, GroupTab>>;
  readonly show: (groupId: string, tab: GroupTab) => void;
  readonly forget: (groupId: string) => void;
}

export const useGroupTab = create<GroupTabState>((set) => ({
  tabs: {},
  show: (groupId, tab) => set((state) => ({ tabs: { ...state.tabs, [groupId]: tab } })),
  forget: (groupId) =>
    set((state) => {
      if (!(groupId in state.tabs)) return state;
      const { [groupId]: _gone, ...kept } = state.tabs;
      return { tabs: kept };
    }),
}));
