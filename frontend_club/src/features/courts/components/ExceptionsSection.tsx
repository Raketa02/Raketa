'use client';

import { useActionState, useState } from 'react';

import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { sentenceFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { SectionHeader } from '@/ui/SectionHeader';
import tableStyles from '@/ui/Table.module.css';

import {
  addException,
  removeException,
  type ExceptionFormState,
  type RemoveState,
} from '../actions';
import { closedCourts, closedWhen, COURTS_COPY, EXCEPTION_REFUSALS } from '../copy';
import type { Court, Exception } from '../mappers';

import styles from './CourtsAndPrices.module.css';
import { ExceptionForm } from './ExceptionForm';

const COPY = COURTS_COPY.exceptions;
const NOTHING_ADDED: ExceptionFormState = {
  refusals: {},
  formRefusal: null,
  added: false,
  bookedThen: null,
};
const NOTHING_REMOVED: RemoveState = { refusal: null };

/**
 * **Exceptions** (the screens B3, the mechanics §16.5): the hours the club has closed and not
 * yet reopened, each with why, when and on which courts, and *+ Add an exception*, whose form
 * takes its place while it is open. One added closes the form; one refused keeps what was
 * typed. *Remove* opens the hours again at once.
 */
export function ExceptionsSection({
  courts,
  exceptions,
  today,
}: {
  courts: readonly Court[];
  exceptions: readonly Exception[];
  today: string;
}) {
  const [state, add, adding] = useActionState(addException, NOTHING_ADDED);
  const [seen, setSeen] = useState(state);
  const [removeState, remove, removing] = useActionState(removeException, NOTHING_REMOVED);
  const [open, setOpen] = useState(false);
  // What the open form shows of the backend's answers: none from before it was opened.
  const [shown, setShown] = useState(NOTHING_ADDED);

  // A new answer: adjust during render, as React recommends over an effect.
  if (seen !== state) {
    setSeen(state);
    if (state.added) setOpen(false);
    else setShown(state);
  }

  const removeSentence = sentenceFor(removeState.refusal, EXCEPTION_REFUSALS);

  return (
    <Card labelledBy="exceptions-title">
      <SectionHeader
        id="exceptions-title"
        title={COPY.title}
        lead={COPY.lead}
        aside={
          open ? undefined : (
            <Button
              type="button"
              onClick={() => {
                setShown(NOTHING_ADDED);
                setOpen(true);
              }}
            >
              {COPY.add}
            </Button>
          )
        }
      />
      {open ? (
        <ExceptionForm
          courts={courts}
          today={today}
          state={shown}
          action={add}
          pending={adding}
          onCancel={() => setOpen(false)}
        />
      ) : null}
      {removeSentence === null ? null : <Notice tone="error">{removeSentence}</Notice>}
      {exceptions.length === 0 ? (
        <p className={styles.none}>{COPY.none}</p>
      ) : (
        <table className={tableStyles.table}>
          <thead className={tableStyles.head}>
            <tr>
              <th scope="col">{COPY.columns.reason}</th>
              <th scope="col">{COPY.columns.when}</th>
              <th scope="col">{COPY.columns.courts}</th>
              <th scope="col">
                <span className="visually-hidden">{COPY.columns.actions}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {exceptions.map((exception) => (
              <tr key={exception.id}>
                <th scope="row" className={styles.name}>
                  {exception.reason}
                </th>
                <td>{closedWhen(exception)}</td>
                <td>{closedCourts(exception, courts)}</td>
                <td>
                  <form action={remove} className={styles.rowActions}>
                    <input type="hidden" name="id" value={exception.id} />
                    <Button type="submit" tone="danger" disabled={removing}>
                      {COPY.remove}
                    </Button>
                  </form>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
