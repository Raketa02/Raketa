/**
 * **A player's payment method: read it, save one, remove it** — pass-throughs, the uniform-strict
 * escape hatch (#552). The rules that make a save land — the Adult attestation, five setups a day,
 * the terms before the secret, the bank's check — are the server's and the provider's, each refusal
 * named in its code; what the checklist does about one is `domain/setupRefusal`.
 *
 * The one thing done here is reading a removal's refusal, because its counts arrive in an untyped
 * dictionary and are parsed on the way in.
 */

import type { AppError } from '@/shared/errors';

import {
  deleteMethod,
  getPaymentMethod,
  postConfirmation,
  postSetup,
  postTerms,
  type Cancellable,
} from '../api/paymentsApi';
import type { MethodInUse, PaymentMethodStanding, SetupOpened } from '../domain/vocabulary';
import { toSetupOpened, toSetupSecret, toStanding } from '../mappers/paymentMappers';
import { methodInUseFrom } from '../schemas/methodInUse';

export async function readPaymentMethod(options: Cancellable = {}): Promise<PaymentMethodStanding> {
  return toStanding(await getPaymentMethod(options));
}

/** Open a setup — step 1's *Continue*. */
export async function openSetup(): Promise<SetupOpened> {
  return toSetupOpened(await postSetup());
}

/**
 * Accept the terms, by the version of the words shown. Answers the open setup's secret — `null`
 * when they were accepted again for the card already saved, whose bank moved it to another brand.
 */
export async function acceptTerms(termsVersion: string): Promise<string | null> {
  return toSetupSecret(await postTerms(termsVersion));
}

/** Save what the phone confirmed. Answers the method as the server now holds it. */
export async function saveConfirmed(): Promise<PaymentMethodStanding> {
  return toStanding(await postConfirmation());
}

export function removePaymentMethod(): Promise<void> {
  return deleteMethod();
}

/** What a refused removal means for the screen. */
export type RemovalRefusal =
  /** A live yes or a booked game ahead still needs it (Q83) — with the counts, when they parse. */
  | { readonly kind: 'IN_USE'; readonly counts: MethodInUse | null }
  /** Nothing is saved any more — removed elsewhere. Re-read. */
  | { readonly kind: 'GONE' }
  | { readonly kind: 'SAY_SO'; readonly error: AppError };

export function removalRefusal(error: AppError): RemovalRefusal {
  if (error.code === 'payment_method_in_use') {
    return { kind: 'IN_USE', counts: methodInUseFrom(error.details) };
  }
  if (error.code === 'payment_method_not_found') return { kind: 'GONE' };
  return { kind: 'SAY_SO', error };
}
