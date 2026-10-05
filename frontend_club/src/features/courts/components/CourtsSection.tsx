'use client';

import { useActionState, useState } from 'react';

import type { Sport } from '@/features/club-details/mappers';
import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import type { RefusalAbout } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { SectionHeader } from '@/ui/SectionHeader';

import { actOnCourt, saveCourt, type CourtActState, type CourtFormState } from '../actions';
import { courtActRefusal, COURTS_COPY } from '../copy';
import type { Court } from '../mappers';

import { CourtDialog, type Confirming } from './CourtDialog';
import { CourtForm } from './CourtForm';
import styles from './CourtsAndPrices.module.css';
import { CourtsTable } from './CourtsTable';

const COPY = COURTS_COPY.courts;
const NOTHING_SAVED: CourtFormState = { refusals: {}, formRefusal: null, saved: null };
const NOTHING_DONE: CourtActState = { done: null, refusal: null };

/**
 * **Courts** (the screens B3, the mechanics §16.4): the table of the club's courts, and the one
 * form that adds a court or edits one, which takes the place of *+ Add a court* while it is
 * open. Switching a court off asks first; switching it on does not. Deleting is the edit form's,
 * and asks first too. A save or a delete that lands closes the form; what was refused stays in
 * it, or over the table.
 */
export function CourtsSection({
  courts,
  sports,
}: {
  courts: readonly Court[];
  /** The sports the club offers: a court plays one of them. */
  sports: readonly Sport[];
}) {
  const [formState, save, saving] = useActionState(saveCourt, NOTHING_SAVED);
  const [seenForm, setSeenForm] = useState(formState);
  const [actState, act, acting] = useActionState(actOnCourt, NOTHING_DONE);
  const [seenAct, setSeenAct] = useState(actState);

  /** The form: adding a court, editing one, or closed. */
  const [editing, setEditing] = useState<'new' | Court | null>(null);
  // What the open form shows of the backend's answers: none from before it was opened.
  const [shown, setShown] = useState(NOTHING_SAVED);
  const [refused, setRefused] = useState<RefusalAbout | null>(null);
  const [confirming, setConfirming] = useState<Confirming | null>(null);

  // A new answer: adjust during render, as React recommends over an effect.
  if (seenForm !== formState) {
    setSeenForm(formState);
    if (formState.saved === null) setShown(formState);
    else setEditing(null);
  }
  if (seenAct !== actState) {
    setSeenAct(actState);
    setRefused(actState.refusal);
    const deleted = actState.done?.act === 'delete' ? actState.done.id : null;
    if (deleted !== null && editing !== null && editing !== 'new' && editing.id === deleted) {
      setEditing(null);
    }
  }

  const open = (court: 'new' | Court) => {
    setShown(NOTHING_SAVED);
    setRefused(null);
    setEditing(court);
  };
  // The court being edited, as the table now shows it: renamed elsewhere, it says so.
  const edited =
    editing === null || editing === 'new'
      ? null
      : (courts.find((each) => each.id === editing.id) ?? editing);

  return (
    <Card labelledBy="courts-title">
      <SectionHeader
        id="courts-title"
        title={COPY.title}
        lead={COPY.lead}
        aside={
          editing === null ? (
            <Button type="button" onClick={() => open('new')}>
              {COPY.add}
            </Button>
          ) : undefined
        }
      />
      {editing === null ? null : (
        <CourtForm
          key={edited?.id ?? 'new'}
          court={edited}
          sports={sports}
          state={shown}
          action={save}
          pending={saving}
          onCancel={() => setEditing(null)}
          onDelete={(court) => setConfirming({ act: 'delete', court })}
        />
      )}
      {refused === null ? null : <Notice tone="error">{courtActRefusal(refused)}</Notice>}
      {courts.length === 0 ? (
        <p className={styles.none}>{COPY.none}</p>
      ) : (
        <CourtsTable
          courts={courts}
          action={act}
          pending={acting}
          onSwitchOff={(court) => setConfirming({ act: 'switch-off', court })}
          onEdit={open}
        />
      )}
      <CourtDialog confirming={confirming} action={act} onClose={() => setConfirming(null)} />
    </Card>
  );
}
