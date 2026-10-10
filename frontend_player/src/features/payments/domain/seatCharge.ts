/**
 * **A share of a game, and the one moment it needs its player** — a payment refused when the game
 * filled, confirmed in the app ([#555](https://github.com/Raketa02/Raketa/issues/555); #541; the
 * mechanics §12.2).
 *
 * Every seat's share is held automatically, *exactly like a subscription*, and taken at the club's
 * cut-off (Q113); only a bank that wants the player present, or a decline, ever brings a share back
 * to them. Then their seat is open again until they confirm it — on the club's account, where the
 * hold was placed — or somebody else takes it.
 */

import type { Sport } from '@/shared/vocabulary/sport';

/**
 * Why a share was refused — the wire's own spelling. Only the first two wait for the player: a
 * changed brand is the terms again, and no method is a setup.
 */
export type ChargeRefusal = 'AUTHENTICATION_REQUIRED' | 'DECLINED' | 'TERMS_NEEDED' | 'NO_METHOD';

/** The club a share is paid to — **the seller**, named on every receipt. */
export interface Seller {
  readonly id: string;
  /** Absent for a club that no longer exists. */
  readonly name?: string;
}

/** One of the reader's seat charges, as the confirmation draws it — never its secret. */
export interface SeatCharge {
  readonly seatChargeId: string;
  /** `null` unless it was refused. */
  readonly refusal: ChargeRefusal | null;
  readonly amountGrosze: number;
  readonly sport: Sport;
  /** The game's hour. */
  readonly startsAt: string;
  readonly club: Seller;
  /** The payment waits for its player now — it can be confirmed. */
  readonly awaitsYou: boolean;
}

/**
 * **What the phone confirms a refused share with** — the provider's key, the club's account and the
 * payment's secret, asked of the server for one press and handed straight to the port. Never cached
 * and never drawn: the setup's own rule for a secret.
 */
export interface PaymentToConfirm {
  readonly publishableKey: string;
  readonly accountId: string;
  readonly clientSecret: string;
}

/** How a refused share is confirmed on the phone — the card on file, or another typed for it. */
export type ConfirmWithCard = 'onFile' | 'typed';

/**
 * **A decline is paid with another card; any other refusal asks the bank about the card on file**
 * (the mechanics §12.2: *confirm it with another card*). The other card pays this share only — the
 * saved method is You › Payments' to change.
 */
export function confirmsWith(charge: Pick<SeatCharge, 'refusal'>): ConfirmWithCard {
  return charge.refusal === 'DECLINED' ? 'typed' : 'onFile';
}
