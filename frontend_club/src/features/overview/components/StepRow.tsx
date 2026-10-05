import type { ComponentProps, ReactNode } from 'react';

import { Notice } from '@/ui/Notice';
import { Tag } from '@/ui/Tag';

import styles from './SetupChecklist.module.css';

/**
 * **One step of the setup checklist**: its number (ticked when done), what it is, why it waits
 * or what was just refused, where it stands, and its one button.
 */
export function StepRow({
  number,
  done,
  title,
  explain,
  why,
  refusal,
  state,
  action,
}: {
  number: number;
  done: boolean;
  title: string;
  explain: string;
  /** Why it waits: the step it is locked behind. */
  why?: string;
  /** What its button was just refused with, as a sentence. */
  refusal?: string | null;
  /** Where it stands: the words on its tag, their tone, and the state they say. */
  state: {
    readonly name: string;
    readonly words: string;
    readonly tone: ComponentProps<typeof Tag>['tone'];
  };
  action?: ReactNode;
}) {
  return (
    <li className={styles.step}>
      <span className={styles.number} data-done={done} aria-hidden="true">
        {number}
      </span>
      <div className={styles.words}>
        <h3 className={styles.title}>{title}</h3>
        <p className={styles.explain}>{explain}</p>
        {why === undefined ? null : <p className={styles.why}>{why}</p>}
        {refusal === null || refusal === undefined ? null : <Notice tone="error">{refusal}</Notice>}
      </div>
      <span className={styles.state} data-state={state.name}>
        <Tag tone={state.tone}>{state.words}</Tag>
      </span>
      <div className={styles.action}>{action}</div>
    </li>
  );
}
