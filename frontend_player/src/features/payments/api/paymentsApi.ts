/**
 * **A player's payment method on the wire** — one of the two layers allowed to read generated
 * types, and the only place these paths are written down
 * ([#552](https://github.com/Raketa02/Raketa/issues/552); the routes are #536's).
 *
 * | | |
 * | --- | --- |
 * | `getPaymentMethod` | `GET …/payment-methods/current` — the saved method, or none |
 * | `postSetup` | `POST …/setup` — open a setup: the key the fields open with, and the terms in force. **Never the secret.** |
 * | `postTerms` | `POST …/terms` — accept the terms; answers the setup's secret (or `null` when accepting again for a card already saved) |
 * | `postConfirmation` | `POST …/confirmation` — the phone has confirmed; read the setup as it stands and save |
 * | `deleteMethod` | `DELETE …/current` — remove it, refused while anything still needs it |
 * | `getSeatCharge` | `GET /seat-charges/{id}` — one of the reader's shares; while it waits for them, what the phone confirms it with (#555) |
 * | `getReceipts` | `GET /players/me/receipts` — every share paid, the latest first (#555) |
 *
 * ## A `signal` on the read and none on the writes
 *
 * `proposalsApi`'s asymmetry, for its reason: a cancelled write can leave a setup opened or a
 * method removed with nobody holding the reply that says so.
 *
 * ## Nothing here is retried
 *
 * Every mutation's rule, and it matters most here: a second `…/setup` spends one of the five a day
 * allows (the card-testing guard) and replaces the first at the provider.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

const METHODS_PATH = '/api/v1/players/me/payment-methods';

/** The read may be abandoned; a write may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

export function getPaymentMethod({ signal }: Cancellable = {}): Promise<
  Schemas['PaymentMethodResponse']
> {
  return httpRequest({
    method: 'GET',
    path: `${METHODS_PATH}/current`,
    authenticated: true,
    signal,
  });
}

/**
 * Open a setup. `adult_attestation_missing` (403) before *Start playing*'s first step,
 * `payment_setups_exhausted` (429) after five in a day, `payments_unavailable` (503).
 */
export function postSetup(): Promise<Schemas['PaymentSetupResponse']> {
  return httpRequest({
    method: 'POST',
    path: `${METHODS_PATH}/setup`,
    authenticated: true,
  });
}

/**
 * Accept the terms the player was shown, by their version. `payment_terms_outdated` (409) when the
 * words are not the terms in force; `payment_setup_not_started` (409) when no setup is open.
 */
export function postTerms(termsVersion: string): Promise<Schemas['PaymentTermsResponse']> {
  const body: Schemas['PaymentTermsRequest'] = { terms_version: termsVersion };
  return httpRequest({
    method: 'POST',
    path: `${METHODS_PATH}/terms`,
    authenticated: true,
    body,
  });
}

/**
 * Save what the phone confirmed. `payment_setup_not_finished`, `payment_method_declined`,
 * `payment_setup_not_started` and `payment_terms_not_accepted` are its 409s.
 */
export function postConfirmation(): Promise<Schemas['PaymentMethodResponse']> {
  return httpRequest({
    method: 'POST',
    path: `${METHODS_PATH}/confirmation`,
    authenticated: true,
  });
}

/** Remove it. `payment_method_in_use` (409, with counts) while anything live needs it. */
export function deleteMethod(): Promise<void> {
  return httpRequest<void>({
    method: 'DELETE',
    path: `${METHODS_PATH}/current`,
    authenticated: true,
  });
}

/**
 * One of the reader's seat charges (#541). While its payment waits for them, `to_confirm` carries
 * the provider's key, the club's account and the payment's secret — **asked of the provider now and
 * recorded nowhere**, so it is read for the press that uses it. `seat_charge_not_found` (404) for a
 * charge that is not theirs; `payments_unavailable` (503).
 */
export function getSeatCharge(
  seatChargeId: string,
  { signal }: Cancellable = {},
): Promise<Schemas['SeatChargeResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/seat-charges/${encodeURIComponent(seatChargeId)}`,
    authenticated: true,
    signal,
  });
}

/** You › Payments' *RECEIPTS*: every share the reader paid, the latest first. */
export function getReceipts({ signal }: Cancellable = {}): Promise<Schemas['ReceiptsResponse']> {
  return httpRequest({
    method: 'GET',
    path: '/api/v1/players/me/receipts',
    authenticated: true,
    signal,
  });
}
