'use client';

import { useState } from 'react';

import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { Form } from '@/ui/Form';
import { sentenceFor } from '@/ui/forms';
import { SectionHeader } from '@/ui/SectionHeader';
import { TextField } from '@/ui/TextField';
import { useFormFeedback } from '@/ui/useFormFeedback';

import type { CheckInState } from '../actions';
import { CHECK_IN_COPY, TYPED_REFUSALS } from '../copy';

import styles from './CheckIn.module.css';

const COPY = CHECK_IN_COPY.typed;

/**
 * **The short code, typed by hand** (the screens B6), for when the camera won't read. A code the
 * page can tell is wrong is said under the box; a player checked in empties it for the next.
 */
export function CodeForm({
  state,
  action,
  checking,
}: {
  state: CheckInState;
  action: (form: FormData) => void;
  checking: boolean;
}) {
  const feedback = useFormFeedback(state);
  const [code, setCode] = useState('');
  const [answered, setAnswered] = useState(state);

  if (answered !== state) {
    setAnswered(state);
    if (state.via === 'typed' && state.checkedIn !== null) setCode('');
  }

  return (
    <Card labelledBy="typed-title">
      <SectionHeader id="typed-title" title={COPY.title} lead={COPY.lead} />
      <Form action={action} className={styles.typed}>
        <input type="hidden" name="via" value="typed" />
        <div className={styles.box}>
          <TextField
            label={COPY.label}
            name="code"
            mono
            autoComplete="off"
            autoCapitalize="characters"
            spellCheck={false}
            value={code}
            onChange={(event) => {
              setCode(event.target.value);
              feedback.edit('code');
            }}
            error={sentenceFor(feedback.refusals.code, TYPED_REFUSALS)}
          />
        </div>
        <Button type="submit" disabled={checking}>
          {checking ? COPY.submitting : COPY.submit}
        </Button>
      </Form>
    </Card>
  );
}
