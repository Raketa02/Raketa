/**
 * **The payments feature's only public surface** — You › Account › Payments: the row on the You
 * tab and the screen behind it ([#552](https://github.com/Rakieta02/Rakieta/issues/552); the screens
 * A7, A7.3).
 *
 * The shell composes the row into the tab's ACCOUNT group; the route file under `you/` mounts the
 * screen. The card fields and the bank's check are the provider's phone half, behind the platform's
 * `PaymentsPort` — nothing here imports Stripe.
 */

export { PaymentsRow, type PaymentsRowProps } from './components/PaymentsRow';
export { PaymentsScreen, type PaymentsScreenProps } from './components/PaymentsScreen';

/**
 * **What the moment a game fills needs of payments** (#555) — the proposals feature runs the yes,
 * and the deck opens the setup, never the reverse:
 *
 * - `PaymentSetupSheet` and `usePaymentSetupNeeded` — a first yes with nothing saved opens the four
 *   steps over the deck, and the yes lands when they are done (A2.4).
 * - `useSeatCharge` and `useConfirmOnPhone` — *Confirm your payment to keep your seat*: the refused
 *   share read, and confirmed on the club's account. The yes again is proposals'.
 * - `paymentKeys` — a booking adds a receipt, so the fill re-reads `paymentKeys.receipts()`, as
 *   `challengeKeys` crosses for the same reason.
 */
export { PaymentSetupSheet, type PaymentSetupSheetProps } from './components/PaymentSetupSheet';
export { paymentMethodQuery, usePaymentSetupNeeded } from './hooks/usePaymentMethod';
export {
  useCardFieldsReady,
  useConfirmOnPhone,
  useSeatCharge,
  type CardFieldsState,
  type PhoneConfirmation,
} from './hooks/useSeatCharge';
export { confirmsWith, type ConfirmWithCard, type SeatCharge } from './domain/seatCharge';
export { paymentKeys } from './hooks/paymentKeys';

/** The words the suites that walk the setup from the deck hold the sheet to (#555). */
export { PAYMENTS_COPY } from './components/paymentsCopy';
