'use server';

import { redirect } from 'next/navigation';

import { writeAsClub } from '@/server/club';
import { saveToldLive } from '@/server/marks';

/** Where Stripe sends the desk back to, and where its pages are left from: the checklist. */
const OVERVIEW = '/overview';
const STRIPE_FAILED = '/overview?notice=stripe-failed';

/** Stripe says the club's account is ready: there is nothing left to fill in. */
const ALREADY_CONNECTED = 'payments_already_connected';

/**
 * **Overview said *You're live***, or the club is not live any more: remember which, in this
 * browser, so the line is said once each time the club goes live.
 */
export async function noteToldLive(told: boolean): Promise<void> {
  await saveToldLive(told === true);
}

/** What *Connect with Stripe* came to when it did not leave for Stripe: the refusal's code. */
export interface ConnectState {
  readonly refusal: string | null;
}

/**
 * A fresh link to Stripe's hosted pages for the club's account, which the first one opens
 * (#537). A link works once, so one is asked for every time.
 */
function askForLink() {
  return writeAsClub((api, auth) => api.POST('/api/v1/club/payments/onboarding-link', auth));
}

/**
 * ***Connect with Stripe***, or ***Continue with Stripe*** (the screens B2): off to Stripe's
 * pages, which send the desk back to Overview. Stripe saying the account is ready already is no
 * refusal: Overview is drawn again, ticked.
 */
export async function connectPayments(): Promise<ConnectState> {
  const outcome = await askForLink();
  if (outcome.ok) redirect(outcome.data.url);
  if (outcome.error.code === ALREADY_CONNECTED) redirect(OVERVIEW);
  return { refusal: outcome.error.code };
}

/**
 * **Where `/payments/continue` sends the desk**: Stripe sends it there when a link is spent or
 * stale, and so does the email *Stripe needs something from you*. A fresh link's pages; Overview
 * when Stripe says the account is ready; or Overview saying Stripe's pages could not be opened.
 */
export async function continueWithStripe(): Promise<string> {
  const outcome = await askForLink();
  if (outcome.ok) return outcome.data.url;
  return outcome.error.code === ALREADY_CONNECTED ? OVERVIEW : STRIPE_FAILED;
}
