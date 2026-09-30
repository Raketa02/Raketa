/**
 * **The payments feature's only public surface** — You › Account › Payments: the row on the You
 * tab and the screen behind it ([#552](https://github.com/Raketa02/Raketa/issues/552); the screens
 * A7, A7.3).
 *
 * The shell composes the row into the tab's ACCOUNT group; the route file under `you/` mounts the
 * screen. The card fields and the bank's check are the provider's phone half, behind the platform's
 * `PaymentsPort` — nothing here imports Stripe.
 */

export { PaymentsRow, type PaymentsRowProps } from './components/PaymentsRow';
export { PaymentsScreen, type PaymentsScreenProps } from './components/PaymentsScreen';
