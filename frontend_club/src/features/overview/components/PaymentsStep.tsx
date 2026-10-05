'use client';

import { useActionState } from 'react';

import { Button } from '@/ui/Button';
import { sentenceFor } from '@/ui/forms';

import { connectPayments, type ConnectState } from '../actions';
import { OVERVIEW_COPY, PAYMENTS_REFUSALS } from '../copy';
import type { PaymentsStatus, StepState } from '../mappers';

import { StepRow } from './StepRow';

const COPY = OVERVIEW_COPY.checklist;
const WORDS = COPY.steps.CONNECT_PAYMENTS;

const NOTHING_REFUSED: ConnectState = { refusal: null };

const TONES = {
  NOT_STARTED: 'amber',
  NEEDS_DETAILS: 'amber',
  READY: 'green',
} as const satisfies Record<PaymentsStatus, string>;

/**
 * ***Connect payments***, the checklist's first step (the screens B2): where Stripe has the
 * club's account, in Stripe's own three states, and until it is ready one button, *Connect with
 * Stripe* or *Continue with Stripe*, which leaves for Stripe's hosted pages. Stripe sends the
 * desk back to Overview. A refusal is said in the row, and the button stays.
 */
export function PaymentsStep({
  number,
  step,
  payments,
}: {
  number: number;
  /** Where the step stands in the checklist: done, or the next to take. */
  step: StepState;
  payments: PaymentsStatus;
}) {
  const [state, connect, connecting] = useActionState(connectPayments, NOTHING_REFUSED);
  return (
    <StepRow
      number={number}
      done={step === 'done'}
      title={WORDS.title}
      explain={WORDS.explain}
      refusal={sentenceFor(state.refusal, PAYMENTS_REFUSALS)}
      state={{ name: payments, words: COPY.payments.states[payments], tone: TONES[payments] }}
      action={
        step === 'done' ? null : (
          <form action={connect}>
            <Button
              type="submit"
              tone={step === 'next' ? 'primary' : 'secondary'}
              disabled={connecting}
            >
              {payments === 'NEEDS_DETAILS' ? COPY.payments.continue : COPY.payments.connect}
            </Button>
          </form>
        )
      }
    />
  );
}
