import { ButtonLink } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { SectionHeader } from '@/ui/SectionHeader';

import { OVERVIEW_COPY } from '../copy';
import type { Setup, SetupStep, StepState } from '../mappers';

import { PaymentsStep } from './PaymentsStep';
import styles from './SetupChecklist.module.css';
import { StepRow } from './StepRow';

const COPY = OVERVIEW_COPY.checklist;

/** Where each step's button goes. Connecting payments leaves for Stripe instead (PaymentsStep). */
const PATHS: Readonly<Record<Exclude<SetupStep, 'CONNECT_PAYMENTS'>, string>> = {
  COURTS: '/courts',
  HOURS_AND_PRICES: '/courts#hours',
  SETTINGS: '/rakieta-settings',
};

const TONES = {
  done: 'green',
  next: 'amber',
  'to-do': 'neutral',
  locked: 'neutral',
} as const satisfies Record<StepState, string>;

/**
 * **The setup checklist** (the screens B2, the mechanics §16.2): the four steps before the
 * club's courts reach anybody's game, each with where it stands and the one button that does
 * it. The next step's button is the page's primary one; a step locked behind another says which,
 * and has none.
 */
export function SetupChecklist({ setup }: { setup: Setup }) {
  return (
    <Card labelledBy="setup-title">
      <SectionHeader id="setup-title" title={COPY.title} lead={COPY.lead} />
      <ol aria-label={COPY.label} className={styles.steps}>
        {setup.steps.map((row, index) => {
          if (row.step === 'CONNECT_PAYMENTS') {
            return (
              <PaymentsStep
                key={row.step}
                number={index + 1}
                step={row.state}
                payments={setup.payments}
              />
            );
          }
          const words = COPY.steps[row.step];
          const locked = row.state === 'locked';
          return (
            <StepRow
              key={row.step}
              number={index + 1}
              done={row.state === 'done'}
              title={words.title}
              explain={words.explain}
              why={locked ? words.locked : undefined}
              state={{ name: row.state, words: COPY.states[row.state], tone: TONES[row.state] }}
              action={
                locked || words.action === undefined ? null : (
                  <ButtonLink
                    href={PATHS[row.step]}
                    tone={row.state === 'next' ? 'primary' : 'secondary'}
                  >
                    {words.action}
                  </ButtonLink>
                )
              }
            />
          );
        })}
      </ol>
    </Card>
  );
}
