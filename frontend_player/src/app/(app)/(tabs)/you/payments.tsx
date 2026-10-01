import { PaymentsScreen } from '@/features/payments/types';
import { LiveYeses, PaymentsToConfirm } from '@/features/proposals/types';

/**
 * *Payments* — pushed over the You tab; `features/payments`' own screen (#552).
 *
 * **Its LIVE YESES are the proposals feature's, composed here** (#554): the yeses are the deck's
 * answers and their details are the deck's screen, and `payments` importing `proposals` would point
 * the edge the wrong way — the deck opens the payment setup, not the reverse. So are its *TO CONFIRM*
 * (#555), refused shares waiting for the player, confirmed through the fill.
 */
export default function PaymentsRoute() {
  return <PaymentsScreen toConfirm={<PaymentsToConfirm />} liveYeses={<LiveYeses />} />;
}
