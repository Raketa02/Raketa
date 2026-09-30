import { PaymentsScreen } from '@/features/payments/types';
import { LiveYeses } from '@/features/proposals/types';

/**
 * *Payments* — pushed over the You tab; `features/payments`' own screen (#552).
 *
 * **Its LIVE YESES are the proposals feature's, composed here** (#554): the yeses are the deck's
 * answers and their details are the deck's screen, and `payments` importing `proposals` would point
 * the edge the wrong way — the deck opens the payment setup, not the reverse.
 */
export default function PaymentsRoute() {
  return <PaymentsScreen liveYeses={<LiveYeses />} />;
}
