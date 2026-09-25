/**
 * **The Friends tab's Competitive · For fun** — held in memory while the app is open, and nowhere
 * else ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §5, PRD #500 story 68).
 *
 * A store rather than the tab's own state because the switch has to **keep its position** when the
 * player leaves the page and comes back, which a component's state does not survive; process-scoped
 * rather than on the phone because §5 lists it among what is *not* remembered. It is one value for
 * the app rather than one per group: the switch sets the intent of the game being built, and a
 * player building one does not change their mind by opening another group.
 *
 * Nothing from the backend is here — it is a choice the player is making, and nothing reads it yet
 * but the switch.
 */

import { create } from 'zustand';

import type { GameIntent } from '../domain/groupPage';

interface GameIntentState {
  readonly intent: GameIntent;
  readonly choose: (intent: GameIntent) => void;
}

export const useGameIntent = create<GameIntentState>((set) => ({
  intent: 'competitive',
  choose: (intent) => set({ intent }),
}));
