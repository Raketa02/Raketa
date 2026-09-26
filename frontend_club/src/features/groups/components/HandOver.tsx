'use client';

import { useActionState, useState } from 'react';

import { Button, ButtonLink } from '@/ui/Button';
import { Card } from '@/ui/Card';
import fieldStyles from '@/ui/Field.module.css';
import { Notice } from '@/ui/Notice';

import { handOverGroup, type HandOverState } from '../actions';
import { GROUPS_COPY, handOverRefusal } from '../copy';
import type { HandOverView } from '../mappers';

import { HandOverDialog } from './HandOverDialog';
import styles from './HandOver.module.css';
import { RunBy } from './RunBy';

const COPY = GROUPS_COPY.handOver;
const NOTHING_REFUSED: HandOverState = { refusal: null };

/**
 * **Hand over** (#500 stories 108–110): who runs the group now, or that nobody does, and the
 * club's active administrators to give it to, or, with nobody to give it to, the way to invite
 * somebody. Choosing posts nothing: only the question's *Hand over* does, so no key can skip the
 * question. A handover that lands goes back to the table.
 */
export function HandOver({ group, choices }: HandOverView) {
  const [state, action, pending] = useActionState(handOverGroup, NOTHING_REFUSED);
  const [chosenId, setChosenId] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  // Somebody the page no longer offers (removed meanwhile) is nobody chosen.
  const chosen = choices.find((choice) => choice.id === chosenId) ?? null;

  return (
    <Card>
      {state.refusal === null ? null : (
        <Notice tone="error">{handOverRefusal(state.refusal)}</Notice>
      )}
      <div className={styles.now}>
        <p className={fieldStyles.label}>{COPY.administrator}</p>
        <p className={styles.runBy}>
          <RunBy administrator={group.administrator} />
        </p>
      </div>
      {choices.length === 0 ? (
        <div className={styles.section}>
          <p className={fieldStyles.label}>{COPY.to}</p>
          <p className={styles.explain}>{COPY.nobody(group.administrator !== null)}</p>
          <div className={styles.buttons}>
            <ButtonLink href="/administrators" tone="primary">
              {COPY.inviteFirst}
            </ButtonLink>
          </div>
        </div>
      ) : (
        <div className={styles.section}>
          <fieldset className={fieldStyles.group}>
            <legend className={fieldStyles.legend}>{COPY.to}</legend>
            <ul className={styles.choices}>
              {choices.map((choice) => (
                <li key={choice.id}>
                  <label className={styles.choice}>
                    <input
                      type="radio"
                      name="administrator"
                      value={choice.id}
                      checked={choice.id === chosen?.id}
                      onChange={() => setChosenId(choice.id)}
                      className={styles.radio}
                    />
                    <span className={styles.who}>
                      <span className={styles.name}>{choice.name}</span>{' '}
                      <span className={styles.email}>{choice.email}</span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          </fieldset>
          <div className={styles.buttons}>
            <ButtonLink href="/groups" tone="outline">
              {COPY.cancel}
            </ButtonLink>
            <Button
              type="button"
              disabled={chosen === null || pending}
              onClick={() => setConfirming(true)}
            >
              {pending ? COPY.submitting : COPY.submit}
            </Button>
          </div>
          <p className={styles.explain}>{COPY.explain}</p>
        </div>
      )}
      <HandOverDialog
        group={group}
        to={confirming ? chosen : null}
        action={action}
        onClose={() => setConfirming(false)}
      />
    </Card>
  );
}
