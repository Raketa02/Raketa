'use client';

import { useState } from 'react';

import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import fieldStyles from '@/ui/Field.module.css';
import { Form } from '@/ui/Form';
import { hasRefusals, sentenceFor, sentencesFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { TextField } from '@/ui/TextField';
import { useFormFeedback } from '@/ui/useFormFeedback';

import type { InviteState } from '../actions';
import { ADMINISTRATORS_COPY, INVITE_REFUSALS } from '../copy';
import { checkInvitation, EMPTY_INVITATION, type Invitation } from '../schemas';

import styles from './InviteForm.module.css';

const COPY = ADMINISTRATORS_COPY.form;

/**
 * **+ Add administrator's form** (club mock 3): a name and an email, then *Cancel* and *Send
 * invitation*, which stays disabled until both would be accepted: by this site's checks, and by
 * the backend's last answer until the box it was about changes. Its owner holds the action, so
 * that a sent invitation can close the form and raise the banner in its place.
 */
export function InviteForm({
  state,
  action,
  pending,
  onCancel,
}: {
  state: InviteState;
  action: (form: FormData) => void;
  pending: boolean;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<Invitation>(EMPTY_INVITATION);
  const feedback = useFormFeedback(state);

  const sentences = sentencesFor(feedback.refusals, INVITE_REFUSALS);
  const formSentence = sentenceFor(feedback.formRefusal, INVITE_REFUSALS);
  const ready = !hasRefusals(checkInvitation(draft)) && !hasRefusals(feedback.refusals);

  return (
    <Card>
      <Form action={action} className={styles.form}>
        {formSentence === null ? null : <Notice tone="error">{formSentence}</Notice>}
        <div className={styles.row}>
          <TextField
            label={COPY.name}
            name="name"
            placeholder={COPY.namePlaceholder}
            autoComplete="off"
            // The desk pressed + Add administrator to type a name.
            autoFocus
            value={draft.name}
            onChange={(event) => {
              setDraft({ ...draft, name: event.target.value });
              feedback.edit('name');
            }}
            error={sentences.name}
          />
          <TextField
            label={COPY.email}
            name="email"
            type="email"
            placeholder={COPY.emailPlaceholder}
            autoComplete="off"
            value={draft.email}
            onChange={(event) => {
              setDraft({ ...draft, email: event.target.value });
              feedback.edit('email');
            }}
            error={sentences.email}
          />
          <div className={styles.buttons}>
            {/* As tall as a box's label, so the buttons stand level with the boxes. */}
            <span className={`${fieldStyles.label} ${styles.spacer}`} aria-hidden="true">
              {COPY.name}
            </span>
            <div className={styles.buttonRow}>
              <Button type="button" tone="outline" onClick={onCancel}>
                {COPY.cancel}
              </Button>
              <Button type="submit" disabled={!ready || pending}>
                {pending ? COPY.sending : COPY.send}
              </Button>
            </div>
          </div>
        </div>
        <p className={styles.explain}>{COPY.explain}</p>
      </Form>
    </Card>
  );
}
