/**
 * Whether a standby join has already carried the explainer this app session.
 *
 * Ephemeral UI state, feature-scoped, and the only store this feature has. It is
 * not server data and it is not a fact about the player — it is a fact about
 * *this run of the app*, which is why it is here and not on the account.
 *
 * **It is not persisted, and it cannot be.** `ADR-0061` says *the first standby
 * join*, which would want a durable flag; nothing on this phone stores one
 * except the OS keychain, which holds credentials and nothing else, and
 * `AsyncStorage` is banned outright. Onboarding's deferred runs take exactly
 * this shape for exactly this reason — the deferral lasts one app session, and
 * the next launch behaves as though it had never happened.
 *
 * **The OS holds the rest of the answer, and it is the durable half.** A player
 * who tapped *Turn on* never meets the explainer again on any launch, because
 * the prompt is spent and `promptIsAvailable` reads that from the platform. So
 * the only person this store's session scope can reach twice is one who declined
 * and then joined a queue in two different sessions.
 */

import { create } from 'zustand';

interface StandbyAskState {
  readonly askedThisSession: boolean;
  readonly markAsked: () => void;
  readonly reset: () => void;
}

export const useStandbyAskStore = create<StandbyAskState>((set) => ({
  askedThisSession: false,
  markAsked: () => set({ askedThisSession: true }),
  reset: () => set({ askedThisSession: false }),
}));
