/**
 * **Which tab a group's page is on** — held for as long as the page is up, and dropped with it
 * ([#558](https://github.com/Raketa02/Raketa/issues/558)).
 *
 * It was the page's own state, and one screen pushed over the page has to read it and move it:
 * ***Post a game*** reads the tab the page stands on as it opens — its **origin**, which a back-out
 * returns to and its chevron names (*Back to Games*) — and leaves it alone until **a post lands**, or
 * a join from a cell's sheet does: then it sets the page's tab to **You’re in**, under it, unseen, a
 * moment before it uncovers it, so the player sees the game they made (#848; #847 set it on opening).
 * Any of the four tabs is an entry (`GROUP_TABS`); none means the page is on its opening tab.
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
