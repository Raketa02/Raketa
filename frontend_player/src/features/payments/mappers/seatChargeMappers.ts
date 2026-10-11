/**
 * **A seat charge and the receipts, off the wire** (#555) — pure. What is dropped on the way in is
 * named: a charge's status beyond *does it wait for you* (the confirmation asks nothing else of it),
 * its proposal (the caller already holds the game), and — on the read the sheet draws — **the
 * payment's secret**, which only `toPaymentToConfirm` reads, for the press that hands it to the port.
 */

import { toSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';

import type { Receipt } from '../domain/receipts';
import type { PaymentToConfirm, SeatCharge, Seller } from '../domain/seatCharge';

type Schemas = components['schemas'];

function toSeller(wire: Schemas['SellerSchema']): Seller {
  return wire.name === null ? { id: wire.id } : { id: wire.id, name: wire.name };
}

/** `undefined` for a sport this build cannot name — the sheet says the charge cannot be read. */
export function toSeatCharge(wire: Schemas['SeatChargeResponse']): SeatCharge | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;
  return {
    seatChargeId: wire.seat_charge_id,
    refusal: wire.refusal,
    amountGrosze: wire.amount_grosze,
    sport,
    startsAt: wire.starts_at,
    club: toSeller(wire.club),
    awaitsYou: wire.to_confirm !== null,
  };
}

/** What the phone confirms with — `null` once the payment no longer waits for the player. */
export function toPaymentToConfirm(wire: Schemas['SeatChargeResponse']): PaymentToConfirm | null {
  const ask = wire.to_confirm;
  if (ask === null) return null;
  return {
    publishableKey: ask.publishable_key,
    accountId: ask.connected_account_id,
    clientSecret: ask.client_secret,
  };
}

function toReceipt(wire: Schemas['ReceiptSchema']): Receipt | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;
  const kept = wire.card_fee_grosze;
  return {
    seatChargeId: wire.seat_charge_id,
    kind: wire.kind,
    club: toSeller(wire.club),
    sport,
    startsAt: wire.starts_at,
    amountGrosze: wire.amount_grosze,
    // The read sends a fee kept on a refund alone.
    ...(wire.kind === 'REFUND' && kept !== null ? { keptGrosze: kept } : {}),
    movedAt: wire.paid_at,
  };
}

/** The list in the server's order — a row whose sport this build cannot name is left out. */
export function toReceipts(wire: Schemas['ReceiptsResponse']): readonly Receipt[] {
  return wire.receipts.map(toReceipt).filter((row): row is Receipt => row !== undefined);
}
