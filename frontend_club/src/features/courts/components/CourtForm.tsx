'use client';

import { useState } from 'react';

import { sportName, type Sport } from '@/features/club-details/mappers';
import { Button } from '@/ui/Button';
import { Choices } from '@/ui/Choices';
import { Form } from '@/ui/Form';
import { sentenceFor, sentencesFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { TextField } from '@/ui/TextField';
import { useFormFeedback } from '@/ui/useFormFeedback';

import type { CourtFormState } from '../actions';
import { COURT_REFUSALS, courtFormRefusal, COURTS_COPY } from '../copy';
import type { Court } from '../mappers';
import { courtDraftOf, EMPTY_COURT, type CourtDraft } from '../schemas';

import styles from './CourtsAndPrices.module.css';

const COPY = COURTS_COPY.courts;

type IndoorOrOutdoor = 'indoor' | 'outdoor';

const INDOOR_OR_OUTDOOR = [
  { value: 'indoor', label: COPY.indoorOrOutdoor.indoor },
  { value: 'outdoor', label: COPY.indoorOrOutdoor.outdoor },
] as const satisfies readonly { value: IndoorOrOutdoor; label: string }[];

function chosenOf(indoor: boolean | null): IndoorOrOutdoor | null {
  if (indoor === null) return null;
  return indoor ? 'indoor' : 'outdoor';
}

function submitLabel(adding: boolean, pending: boolean): string {
  if (adding) return pending ? COPY.form.adding : COPY.form.add;
  return pending ? COPY.form.saving : COPY.form.save;
}

/**
 * ***Add a court*, or *Edit Court 2*** (the screens B3): a name, one of the club's sports, and
 * indoor or outdoor, which a player's card shows. An edit adds *Delete court*, which asks first.
 * Its owner holds the action, so that a court saved can close the form.
 */
export function CourtForm({
  court,
  sports,
  state,
  action,
  pending,
  onCancel,
  onDelete,
}: {
  /** The court being edited, or `null` for a new one. */
  court: Court | null;
  sports: readonly Sport[];
  state: CourtFormState;
  action: (form: FormData) => void;
  pending: boolean;
  onCancel: () => void;
  onDelete: (court: Court) => void;
}) {
  const [draft, setDraft] = useState<CourtDraft>(() =>
    court === null ? EMPTY_COURT : courtDraftOf(court),
  );
  const feedback = useFormFeedback(state);
  const sentences = sentencesFor(feedback.refusals, COURT_REFUSALS);
  const formSentence =
    feedback.formRefusal === null
      ? null
      : court === null
        ? sentenceFor(feedback.formRefusal, COURT_REFUSALS)
        : courtFormRefusal({ code: feedback.formRefusal, name: court.name });

  return (
    <div className={styles.subform}>
      <Form action={action} className={styles.form}>
        <h3 className={styles.formTitle}>
          {court === null ? COPY.form.addTitle : COPY.form.editTitle(court.name)}
        </h3>
        {formSentence === null ? null : <Notice tone="error">{formSentence}</Notice>}
        <input type="hidden" name="id" value={court?.id ?? ''} />
        <TextField
          label={COPY.form.name}
          name="name"
          placeholder={COPY.form.namePlaceholder}
          autoComplete="off"
          // The desk pressed + Add a court, or Edit, to type.
          autoFocus
          value={draft.name}
          onChange={(event) => {
            setDraft({ ...draft, name: event.target.value });
            feedback.edit('name');
          }}
          error={sentences.name}
        />
        <Choices
          legend={COPY.form.sport}
          name="sport"
          options={sports.map((sport) => ({ value: sport, label: sportName(sport) }))}
          value={draft.sport}
          onChange={(sport) => {
            setDraft({ ...draft, sport });
            feedback.edit('sport');
          }}
          error={sentences.sport}
        />
        <Choices
          legend={COPY.form.indoor}
          name="indoor"
          options={INDOOR_OR_OUTDOOR}
          value={chosenOf(draft.indoor)}
          onChange={(chosen) => {
            setDraft({ ...draft, indoor: chosen === 'indoor' });
            feedback.edit('indoor');
          }}
          error={sentences.indoor}
        />
        <div className={styles.buttons}>
          <Button type="button" tone="outline" onClick={onCancel}>
            {COPY.form.cancel}
          </Button>
          <Button type="submit" disabled={pending}>
            {submitLabel(court === null, pending)}
          </Button>
          {court === null ? null : (
            <span className={styles.delete}>
              <Button type="button" tone="danger" onClick={() => onDelete(court)}>
                {COPY.form.delete}
              </Button>
            </span>
          )}
        </div>
      </Form>
    </div>
  );
}
