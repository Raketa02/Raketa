/**
 * **The handovers the sheet closed, for this launch**
 * ([ADR-0192](../../../../../docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md)
 * §2).
 *
 * Closing the sheet tells the server, and the server is what remembers it for every phone. This
 * holds the gap between the two: a re-read that lands before the write — or a write that could not
 * reach the server — would otherwise put the same sheet straight back up. So it lives in memory and
 * dies with the process, as `invitationsSetAside` does; a write that never landed is told again on
 * the next launch, which is the honest answer.
 */

import { create } from 'zustand';

interface HandoversClosedState {
  /** The groups whose handover the sheet told and was closed on, since launch. */
  readonly closed: readonly string[];
  readonly close: (groupIds: readonly string[]) => void;
  readonly reset: () => void;
}

export const useHandoversClosed = create<HandoversClosedState>((set) => ({
  closed: [],
  close: (groupIds) =>
    set((state) => ({
      closed: [...state.closed, ...groupIds.filter((id) => !state.closed.includes(id))],
    })),
  reset: () => set({ closed: [] }),
}));
