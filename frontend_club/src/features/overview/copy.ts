/**
 * **Overview's words**: the setup checklist until the club is live (the screens B2), with where
 * Stripe has the club's account; then once, *You're live*, and after that, that the club is live
 * on Raketa.
 */

import type { PaymentsStatus, SetupStep, StepState } from './mappers';

interface StepWords {
  readonly title: string;
  /** What the step is, under its title. */
  readonly explain: string;
  /** Its one button, when this site can do it. */
  readonly action?: string;
  /** Why it is locked: the step it waits for. */
  readonly locked?: string;
}

const STEPS: Readonly<Record<SetupStep, StepWords>> = {
  CONNECT_PAYMENTS: {
    title: 'Connect payments',
    explain: 'You are the seller: players pay your own Stripe account, and it pays you out.',
  },
  COURTS: {
    title: 'Add your courts',
    explain: 'Each court with its sport, indoor or outdoor.',
    action: 'Add courts',
  },
  HOURS_AND_PRICES: {
    title: 'Set hours and prices',
    explain: 'The hours of the week each court is offered, and what a court-hour costs.',
    action: 'Set hours and prices',
    locked: 'Once you add a court.',
  },
  SETTINGS: {
    title: 'Check the settings',
    explain: 'The release lead and the cut-off; then confirm them.',
    action: 'Check the settings',
  },
};

export const OVERVIEW_COPY = {
  live: "You're live — your courts can now be booked through Raketa.",
  /** Once the club is live, in the checklist's place (Q121). */
  liveOnRaketa: {
    title: 'Live on Raketa',
    lead: 'Every game booked on your courts through Raketa is in Bookings, a day at a time.',
    today: 'Today’s bookings',
  },
  checklist: {
    title: 'Before your courts can be booked',
    lead: "Your courts reach players' games once all four are done.",
    /** The list, as a screen reader names it. */
    label: 'Setup checklist',
    states: {
      done: 'done ✓',
      next: 'next',
      'to-do': 'to do',
      locked: 'locked',
    } satisfies Record<StepState, string>,
    steps: STEPS,
    /** *Connect payments*' own states, in the row's place for a state, and its one button. */
    payments: {
      states: {
        NOT_STARTED: 'not started',
        NEEDS_DETAILS: 'Stripe needs more details',
        READY: 'ready ✓',
      } satisfies Record<PaymentsStatus, string>,
      connect: 'Connect with Stripe',
      continue: 'Continue with Stripe',
    },
  },
  /** Stripe's pages could not be opened from `/payments/continue`. */
  stripeFailed: "We couldn't open Stripe's pages just now. Try again in a moment.",
} as const;

/** What *Connect with Stripe* can be refused with; the rest are every form's. */
export const PAYMENTS_REFUSALS: Readonly<Record<string, string>> = {
  payments_unavailable: "We couldn't reach Stripe. Try again in a moment.",
};
