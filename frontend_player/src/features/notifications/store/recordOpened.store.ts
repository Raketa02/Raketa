/**
 * **Whose record a notice opened** — *You're friends* lands on the new friend's record (#753), and a
 * record is a sheet rather than a screen, so there is no route to push. A tap — on a row of the list,
 * the banner, or the phone's own notification — names the person here, and `NoticesHost`, which is
 * up for as long as the tabs are, draws their record over wherever the player is. Closing it forgets
 * them.
 *
 * Feature-scoped, process-scoped and never on the phone: it is one screen's worth of UI state shared
 * by three places that open notices, and nothing from the server — the record reads itself.
 */

import { create } from 'zustand';

interface RecordOpenedState {
  readonly playerId: string | undefined;
  readonly open: (playerId: string) => void;
  readonly close: () => void;
}

export const useRecordOpened = create<RecordOpenedState>((set) => ({
  playerId: undefined,
  open: (playerId) => set({ playerId }),
  close: () => set({ playerId: undefined }),
}));
