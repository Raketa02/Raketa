import { redirect } from 'next/navigation';

import { continueWithStripe } from '@/features/overview/actions';

/**
 * **Where Stripe sends a desk whose link was spent or went stale**, and where the email *Stripe
 * needs something from you* points (#537): a fresh link to Stripe's pages, followed at once. A
 * link works once, so this is a door, never a page.
 */
export async function GET() {
  redirect(await continueWithStripe());
}
