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
 * **locked** behind the step it needs, or **pending**: *Connect payments*, which nothing on this
 * site can do until connecting Stripe is built here (#562).
 */
export type StepState = 'done' | 'next' | 'to-do' | 'locked' | 'pending';

export interface SetupRow {
  readonly step: SetupStep;
  readonly state: StepState;
}

export interface Setup {
  readonly steps: readonly SetupRow[];
  /** Every step done: the club's courts can reach players' decks. */
  readonly live: boolean;
}

function stateOf(step: SetupStep, state: WireSetup['steps'][number]['state']): StepState {
  if (state === 'DONE') return 'done';
  if (step === 'CONNECT_PAYMENTS') return 'pending';
  return state === 'LOCKED' ? 'locked' : 'to-do';
}

/** Which step is next is the first one to do, read off the order (the backend's rule, #535). */
export function toSetup(wire: WireSetup): Setup {
  const steps = wire.steps.map(({ step, state }) => ({ step, state: stateOf(step, state) }));
  const next = steps.findIndex((row) => row.state === 'to-do');
  return {
    steps: steps.map((row, index) => (index === next ? { ...row, state: 'next' } : row)),
    live: wire.live,
  };
}

/** Whether one step of the checklist is done. */
export function stepDone(setup: Setup, step: SetupStep): boolean {
  return setup.steps.some((row) => row.step === step && row.state === 'done');
}
