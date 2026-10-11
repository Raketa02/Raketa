/**
 * The agreement between the domain's unions and the contract — asserted by the compiler, over
 * the one `Exact` in `@/shared/vocabulary/wireAgreement`, as `proposals` and `games` assert theirs.
 * A wallet added, removed or renamed on the wire fails here, where the method card's badge and the
 * row's line are keyed by it; so does a refusal, which the confirmation is worded by.
 * A receipt's kind is one of them too: refunds joined the list with the leaving rules (#544), and
 * a hold let go (`RELEASED`) with the holds (#641, #644).
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { ReceiptKind } from '../domain/receipts';
import type { ChargeRefusal } from '../domain/seatCharge';
import type { Wallet } from '../domain/vocabulary';

type Schemas = components['schemas'];

export const PAYMENTS_VOCABULARY_AGREES: {
  readonly wallet: Exact<Wallet, Schemas['Wallet']>;
  readonly chargeRefusal: Exact<ChargeRefusal, Schemas['FailureReason']>;
  readonly receiptKind: Exact<ReceiptKind, Schemas['ReceiptSchema']['kind']>;
} = { wallet: true, chargeRefusal: true, receiptKind: true };
