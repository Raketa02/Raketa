/**
 * **The setup checklist, wire to view.** The only file in this feature that imports a generated
 * type (ADR-0187 §6); everything else reads the {@link Setup} it makes.
 */

import type { components } from '@/generated/schema';

type WireSetup = components['schemas']['SetupResponse'];

/** The five steps, in the order the backend lists them and Overview draws them. */
export type SetupStep = components['schemas']['SetupStep'];

/**
 * Where a step stands, as its row says it: **done**, **next** (the first left to do), **to do**,
 * or **locked** behind the step it needs.
 */
export type StepState = 'done' | 'next' | 'to-do' | 'locked';

/**
 * **Where the club's Stripe account stands**, in the first step's words (#537): not started,
 * Stripe needs more details, or ready. Ready can be lost, when Stripe wants more later.
 */
export type PaymentsStatus = components['schemas']['PaymentsStatus'];

export interface SetupRow {
  readonly step: SetupStep;
  readonly state: StepState;
}

export interface Setup {
  readonly steps: readonly SetupRow[];
  /** Every step done: the club's courts can reach players' decks. */
  readonly live: boolean;
  /** The first step's own words: done is *ready*, and to do is one of the other two. */
  readonly payments: PaymentsStatus;
}

function stateOf(state: WireSetup['steps'][number]['state']): StepState {
  if (state === 'DONE') return 'done';
  return state === 'LOCKED' ? 'locked' : 'to-do';
}

/** Which step is next is the first one to do, read off the order (the backend's rule, #535). */
export function toSetup(wire: WireSetup): Setup {
  const steps = wire.steps.map(({ step, state }) => ({ step, state: stateOf(state) }));
  const next = steps.findIndex((row) => row.state === 'to-do');
  return {
    steps: steps.map((row, index) => (index === next ? { ...row, state: 'next' } : row)),
    live: wire.live,
    payments: wire.payments,
  };
}

/** Whether one step of the checklist is done. */
export function stepDone(setup: Setup, step: SetupStep): boolean {
  return setup.steps.some((row) => row.step === step && row.state === 'done');
}
