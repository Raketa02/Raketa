/**
 * **The Games deck's Competitive · For fun** — which kind the deck stands on, picked in the Games
 * tab's menu since #862 (the switch above the deck before), and the kind *Post a game* starts on;
 * held in memory while the app is open, and nowhere else
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §5, PRD #500 story 68).
 *
 * A store rather than the tab's own state because the kind has to **keep its position** when the
 * player leaves the page and comes back, which a component's state does not survive, and because a
 * notice opening the deck at a card moves it from the page (#559); process-scoped rather than on the
 * phone because §5 lists it among what is *not* remembered. One value for the app rather than one
 * per group.
 *
 * **The Friends tab's kind is not this one** since #757 — picked in that tab's menu since #861, where
 * a switch above the court stood: it sets one game's kind (`friendsGame.store`), and picking it never
 * moves the deck.
 *
 * Nothing from the backend is here — it is a choice the player is making.
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
