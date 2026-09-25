'use client';

import { useActionState, useState } from 'react';

import { Button } from '@/ui/Button';
import { Form } from '@/ui/Form';
import { Card } from '@/ui/Card';
import { sentenceFor, sentencesFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { useFormFeedback } from '@/ui/useFormFeedback';

import { saveClubDetails, type DetailsFormState } from '../actions';
import { DETAILS_COPY, DETAILS_REFUSALS } from '../copy';
import type { Club, MapSettings } from '../mappers';
import { draftOf, type DetailsDraft } from '../schemas';

import { ClubDetailsFields } from './ClubDetailsFields';
import styles from './ClubDetailsForm.module.css';

const NOTHING_YET: DetailsFormState = { refusals: {}, formRefusal: null, saved: null };

/**
 * **Club details** (#500 story 93): every sign-up detail, editable at any time, with the server's
 * refusals under the field they name. A save that lands puts the details as the backend
 * recorded them back into the boxes (names trimmed and collapsed) and says so.
 */
export function ClubDetailsForm({ club, map }: { club: Club; map: MapSettings }) {
  const [state, formAction, pending] = useActionState(saveClubDetails, NOTHING_YET);
  const [draft, setDraft] = useState<DetailsDraft>(() => draftOf(club));
  const [answered, setAnswered] = useState(state);
  const feedback = useFormFeedback(state);

  if (answered !== state) {
    setAnswered(state);
    if (state.saved !== null) setDraft(draftOf(state.saved));
  }

  const sentences = sentencesFor(feedback.refusals, DETAILS_REFUSALS);
  const formSentence = sentenceFor(feedback.formRefusal, DETAILS_REFUSALS);

  return (
    <Card>
      <Form action={formAction} className={styles.form}>
        {formSentence === null ? null : <Notice tone="error">{formSentence}</Notice>}
        <ClubDetailsFields
          draft={draft}
          onChange={(next, field) => {
            setDraft(next);
            feedback.edit(field);
          }}
          refusals={sentences}
          map={map}
        />
        <div className={styles.actions}>
          <Button type="submit" disabled={pending}>
            {pending ? DETAILS_COPY.saving : DETAILS_COPY.save}
          </Button>
          {state.saved !== null && !feedback.touched ? (
            <Notice tone="success">{DETAILS_COPY.saved}</Notice>
          ) : null}
        </div>
      </Form>
    </Card>
  );
}
