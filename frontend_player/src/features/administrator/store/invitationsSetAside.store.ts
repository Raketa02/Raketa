/**
 * **The invitations set aside with *Not now*, for this launch** (PRD #500 story 119, ADR-0184 §2).
 *
 * *Not now* hides the sheet until the next launch, and it comes back until the invitation is
 * accepted or expires. That is a fact about this process and nothing else — not server data, since
 * the invitation is still open, and not the phone's, since the next launch must offer it again — so
 * it is held in memory and dies with the process. `onboarding`'s set-aside runs are the same shape
 * for the same reason.
 */

import { create } from 'zustand';

interface InvitationsSetAsideState {
  /** The administrator ids offered and set aside since launch. */
  readonly setAside: readonly string[];
  readonly setAsideOne: (administratorId: string) => void;
  readonly reset: () => void;
}

export const useInvitationsSetAside = create<InvitationsSetAsideState>((set) => ({
  setAside: [],
  setAsideOne: (administratorId) =>
    set((state) =>
      state.setAside.includes(administratorId)
        ? state
        : { setAside: [...state.setAside, administratorId] },
    ),
  reset: () => set({ setAside: [] }),
}));
