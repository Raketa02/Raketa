/**
 * **The payments feature's query keys** — one entry today: the saved method, which the You tab's
 * row and the Payments screen both read, and which a save, a removal and a re-accepted term all
 * write or re-read.
 */

export const paymentKeys = {
  all: ['payments'] as const,
  /** `GET …/payment-methods/current`. */
  current: () => [...paymentKeys.all, 'current'] as const,
};
