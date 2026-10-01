/**
 * The agreement between the domain's unions and the contract — asserted by the compiler, over
 * the one `Exact` in `@/shared/vocabulary/wireAgreement`, as `proposals` and `games` assert theirs.
 * A wallet added, removed or renamed on the wire fails here, where the method card's badge and the
 * row's line are keyed by it; so does a refusal, which the confirmation is worded by.
 *
 * **One agreement is one-way, and says when it stops being.** A receipt's kind is `CHARGE` alone on
 * the wire until refunds join the list (#544), and the row already draws `REFUND` (the screens
 * A7.3) — so what is asserted is that every kind the wire serves is one the row can draw. When
 * #544 serves refunds the two are equal, and this becomes `Exact`.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { ReceiptKind } from '../domain/receipts';
import type { ChargeRefusal } from '../domain/seatCharge';
import type { Wallet } from '../domain/vocabulary';

type Schemas = components['schemas'];

/** Every member of `Wire` is a member of `Ours` — the row can draw whatever the wire serves. */
type DrawsEvery<Ours, Wire> = [Wire] extends [Ours] ? true : false;

export const PAYMENTS_VOCABULARY_AGREES: {
  readonly wallet: Exact<Wallet, Schemas['Wallet']>;
  readonly chargeRefusal: Exact<ChargeRefusal, Schemas['FailureReason']>;
  readonly receiptKind: DrawsEvery<ReceiptKind, Schemas['ReceiptSchema']['kind']>;
} = { wallet: true, chargeRefusal: true, receiptKind: true };
