/**
 * ***Post a game*'s draft** — the four controls, the week shown and the pick, **kept while the player
 * stays in the group** (the screens A5: *back chevron → Fill in, the draft kept*).
 *
 * A store rather than the screen's state because the screen is a route pushed over the group's page,
 * and *back* unmounts it: a player who backs out to Fill in to look at a row and opens *Post a game*
 * again finds what they had chosen. **One draft, for one group**: a draft read for another group is
 * no draft at all (`draftFor`), and the group's page forgets it when it goes (`forgetPostDraft`) — so
 * leaving the group, by its back chevron or by the tab bar laying the stack down, starts the next
 * post from nothing. Process-scoped and never on the phone: it is a choice being made, and ADR-0188
 * §5 keeps such choices in memory.
 *
 * Nothing from the backend is here: the pick holds the court hour the player chose — the day, the
 * range, the club's id and the hour — and the club's name, the share and every count stay the reads'.
 */

import { create } from 'zustand';

import { NEW_DRAFT, type PostDraft } from '../domain/posting';

interface PostDraftState {
  readonly groupId: string | undefined;
  readonly draft: PostDraft;
  /** Write the group's draft — a change made with one of the domain's `with…` rules. */
  readonly keep: (groupId: string, change: (draft: PostDraft) => PostDraft) => void;
  /** Start the group's next post from nothing — after a post, or once its page goes. */
  readonly forget: (groupId: string) => void;
}

export const usePostDraftStore = create<PostDraftState>((set, get) => ({
  groupId: undefined,
  draft: NEW_DRAFT,
  keep: (groupId, change) =>
    set({ groupId, draft: change(get().groupId === groupId ? get().draft : NEW_DRAFT) }),
  forget: (groupId) => {
    if (get().groupId === groupId) set({ groupId: undefined, draft: NEW_DRAFT });
  },
}));

/** The draft for this group — a fresh one when the store holds another group's. */
export function draftFor(state: Pick<PostDraftState, 'groupId' | 'draft'>, groupId: string) {
  return state.groupId === groupId ? state.draft : NEW_DRAFT;
}

/** **The group's page went** — its draft goes with it. Called by the page, through `types.ts`. */
export function forgetPostDraft(groupId: string): void {
  usePostDraftStore.getState().forget(groupId);
}
