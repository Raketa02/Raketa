import { ButtonLink } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { SectionHeader } from '@/ui/SectionHeader';
import { Tag } from '@/ui/Tag';

import { OVERVIEW_COPY } from '../copy';
import type { Setup, SetupStep, StepState } from '../mappers';

import styles from './SetupChecklist.module.css';

const COPY = OVERVIEW_COPY.checklist;

/** Where each step's button goes. Connecting payments goes nowhere here until #562. */
const PATHS: Readonly<Record<SetupStep, string | null>> = {
  CONNECT_PAYMENTS: null,
  WAY_OF_WORKING: '/raketa-settings',
  COURTS: '/courts',
  HOURS_AND_PRICES: '/courts#hours',
  SETTINGS: '/raketa-settings',
};

const TONES = {
  done: 'green',
  next: 'amber',
  'to-do': 'neutral',
  locked: 'neutral',
  pending: 'neutral',
} as const satisfies Record<StepState, string>;

/**
 * **The setup checklist** (the screens B2, the mechanics §16.2): the five steps before the
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
          const words = COPY.steps[row.step];
          const waits = row.state === 'locked' || row.state === 'pending';
          const href = waits ? null : PATHS[row.step];
          const why =
            row.state === 'locked'
              ? words.locked
              : row.state === 'pending'
                ? words.pending
                : undefined;
          return (
            <li key={row.step} className={styles.step}>
              <span className={styles.number} data-done={row.state === 'done'} aria-hidden="true">
                {index + 1}
              </span>
              <div className={styles.words}>
                <h3 className={styles.title}>{words.title}</h3>
                <p className={styles.explain}>{words.explain}</p>
                {why === undefined ? null : <p className={styles.why}>{why}</p>}
              </div>
              <span className={styles.state} data-state={row.state}>
                <Tag tone={TONES[row.state]}>{COPY.states[row.state]}</Tag>
              </span>
              <div className={styles.action}>
                {href !== null && words.action !== undefined ? (
                  <ButtonLink href={href} tone={row.state === 'next' ? 'primary' : 'secondary'}>
                    {words.action}
                  </ButtonLink>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </Card>
  );
}
