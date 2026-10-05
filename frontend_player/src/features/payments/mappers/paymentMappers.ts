/**
 * **The payment routes' answers, as the screens read them** — the wire boundary, pure
 * (#552). What is dropped on the way in is named: the terms' version on a read, which the
 * checklist takes from the setup it opens rather than from a read that may be minutes old, and the
 * setup's id.
 */

import type { components } from '@/generated/schema';

import type { PaymentMethodStanding, SavedMethod, SetupOpened } from '../domain/vocabulary';

type Schemas = components['schemas'];

export function toSavedMethod(wire: Schemas['SavedMethodSchema']): SavedMethod {
  return { brand: wire.brand, lastFour: wire.last_four, wallet: wire.wallet ?? null };
}

export function toStanding(wire: Schemas['PaymentMethodResponse']): PaymentMethodStanding {
  return {
    method: wire.method === null ? null : toSavedMethod(wire.method),
    // Never asked of a player with nothing saved, whatever a read says.
    termsNeeded: wire.method !== null && wire.terms_needed,
  };
}

/** The setup's id is dropped: the server keeps it against the player, and no call names it. */
export function toSetupOpened(wire: Schemas['PaymentSetupResponse']): SetupOpened {
  return { publishableKey: wire.publishable_key, termsVersion: wire.terms_version };
}

/** The terms' answer: the open setup's secret, or `null` when they were accepted again for a card saved. */
export function toSetupSecret(wire: Schemas['PaymentTermsResponse']): string | null {
  return wire.client_secret;
}
