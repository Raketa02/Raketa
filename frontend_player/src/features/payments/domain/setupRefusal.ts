/**
 * **What a refusal on the way to a saved method costs the checklist next** — `sendRefusal`'s shape
 * (`features/challenges`): a refusal turned into the act the screen owes, whether the server said
 * it or the bank did ([#552](https://github.com/Raketa02/Raketa/issues/552); the routes are #536's).
 *
 * | Said by | Saying | The checklist |
 * | --- | --- | --- |
 * | the bank | *declined* · `payment_method_declined` | Card details again — the same setup can try another card. |
 * | the bank | *cancelled* — the check or the sheet closed | Step 4 stays open, to ask again. |
 * | the bank | *failed* — anything else | Step 4 stays open, to ask again. |
 * | the server | `payment_setup_not_finished` | The check is not done. Step 4 stays open, and asking again re-reads. |
 * | the server | `payment_setup_not_started`, `payment_terms_not_accepted` | No setup is open, or the one read has no terms. Start over. |
 * | the server | `payment_terms_outdated` | The words on this phone are not the terms in force; nothing can be accepted until the app is updated. |
 * | the server | anything else | Say what it says, and move nothing. |
 *
 * **A code and never a status**: four of the server's are `409`.
 */

import type { AppError } from '@/shared/errors';

export type SetupRefusal =
  | { readonly kind: 'CARD_DECLINED' }
  | { readonly kind: 'BANK_CLOSED' }
  | { readonly kind: 'BANK_FAILED' }
  | { readonly kind: 'BANK_NOT_DONE' }
  | { readonly kind: 'START_OVER' }
  | { readonly kind: 'TERMS_OUTDATED' }
  | { readonly kind: 'SAY_SO'; readonly error: AppError };

/**
 * What the open step says went wrong: a refusal as the step draws it — a start-over is said as the
 * setup gone — and the one failure before anybody is asked, the provider not taking what was typed.
 */
export type SetupFailure =
  | Exclude<SetupRefusal, { readonly kind: 'START_OVER' }>
  | { readonly kind: 'SETUP_GONE' }
  | { readonly kind: 'CARD_REFUSED' }
  /** The payment provider would not start on this phone, so there are no card fields to show. */
  | { readonly kind: 'PROVIDER_NOT_STARTED' };

/** Every answer from the bank but *saved* — the provider port's own words for them. */
export type BankRefusal = 'cancelled' | 'declined' | 'failed';

export function setupRefusal(error: AppError): SetupRefusal {
  switch (error.code) {
    case 'payment_method_declined':
      return { kind: 'CARD_DECLINED' };
    case 'payment_setup_not_finished':
      return { kind: 'BANK_NOT_DONE' };
    case 'payment_setup_not_started':
    case 'payment_terms_not_accepted':
      return { kind: 'START_OVER' };
    case 'payment_terms_outdated':
      return { kind: 'TERMS_OUTDATED' };
    default:
      return { kind: 'SAY_SO', error };
  }
}

export function bankRefusal(answer: BankRefusal): SetupRefusal {
  switch (answer) {
    case 'declined':
      return { kind: 'CARD_DECLINED' };
    case 'cancelled':
      return { kind: 'BANK_CLOSED' };
    case 'failed':
      return { kind: 'BANK_FAILED' };
  }
}
