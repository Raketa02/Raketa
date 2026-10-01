/**
 * **The payments feature's query keys** — the saved method, which the You tab's row and the
 * Payments screen both read, and which a save, a removal and a re-accepted term all write or
 * re-read; one refused share, as the confirmation draws it; and the receipts, which a game booked
 * anywhere in the app adds to (#555), so the key crosses `types.ts` for the fill to re-read.
 */

export const paymentKeys = {
  all: ['payments'] as const,
  /** `GET …/payment-methods/current`. */
  current: () => [...paymentKeys.all, 'current'] as const,
  /** `GET /seat-charges/{id}` — the facts, never the secret. */
  seatCharge: (seatChargeId: string) => [...paymentKeys.all, 'seat-charge', seatChargeId] as const,
  /** `GET /players/me/receipts`. */
  receipts: () => [...paymentKeys.all, 'receipts'] as const,
};
