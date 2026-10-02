/** **Overview's words**: the setup checklist until the club is live (the screens B2), then once, *You're live*. */

import type { SetupStep, StepState } from './mappers';

interface StepWords {
  readonly title: string;
  /** What the step is, under its title. */
  readonly explain: string;
  /** Its one button, when this site can do it. */
  readonly action?: string;
  /** Why it is locked: the step it waits for. */
  readonly locked?: string;
  /** Why it is pending: nothing here does it yet. */
  readonly pending?: string;
}

const STEPS: Readonly<Record<SetupStep, StepWords>> = {
  CONNECT_PAYMENTS: {
    title: 'Connect payments',
    explain: 'You are the seller: players pay your own Stripe account, and it pays you out.',
    pending: 'Connecting Stripe opens here soon.',
  },
  WAY_OF_WORKING: {
    title: 'Choose how you work with Raketa',
    explain: 'Only Raketa, Instant or On request.',
    action: 'Choose',
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
    explain: 'The cut-off, and the release lead or the minimum notice; then confirm them.',
    action: 'Check the settings',
    locked: 'Once you choose how you work with Raketa.',
  },
};

export const OVERVIEW_COPY = {
  empty: 'Nothing to show here yet.',
  live: "You're live — your courts can now be booked through Raketa.",
  checklist: {
    title: 'Before your courts can be booked',
    lead: "Your courts reach players' games once all five are done.",
    /** The list, as a screen reader names it. */
    label: 'Setup checklist',
    states: {
      done: 'done ✓',
      next: 'next',
      'to-do': 'to do',
      locked: 'locked',
      pending: 'pending',
    } satisfies Record<StepState, string>,
    steps: STEPS,
  },
} as const;
