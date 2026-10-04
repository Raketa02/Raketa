'use client';

import { useActionState, useState } from 'react';

import { Button } from '@/ui/Button';
import { Form } from '@/ui/Form';
import { blankForm, sentenceFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { TextField } from '@/ui/TextField';
import { TextLink } from '@/ui/TextLink';
import { useFormFeedback } from '@/ui/useFormFeedback';

import { claimCode } from '../actions';
import { isSpent, RESET_COPY, RESET_REFUSALS } from '../copy';
import type { CodeField } from '../schemas';

import styles from './forms.module.css';

/**
 * **Enter the code**: the email and the 8-character code from it, exchanged for a ticket the new
 * password is set with. A wrong code is said under the code box; a spent one, over the form,
 * with the way to ask again.
 */
export function ResetCodeForm({ email: offered }: { email: string }) {
  const [state, formAction, pending] = useActionState(claimCode, blankForm<CodeField>());
  const feedback = useFormFeedback(state);
  const [email, setEmail] = useState(offered);
  const [code, setCode] = useState('');
  const refusals = RESET_REFUSALS.code;
  const formSentence = sentenceFor(feedback.formRefusal, refusals);

  return (
    <Form action={formAction} className={styles.form}>
      <h2 className={styles.heading}>{RESET_COPY.code.title}</h2>
      <p className={styles.lead}>{RESET_COPY.code.lead}</p>
      {formSentence === null ? null : (
        <Notice tone="error">
          {formSentence}
          {isSpent(feedback.formRefusal) ? (
            <TextLink href="/forgot-password">{RESET_COPY.code.askAgain}</TextLink>
          ) : null}
        </Notice>
      )}
      <TextField
        label={RESET_COPY.code.email}
        name="email"
        type="email"
        autoComplete="username"
        value={email}
        onChange={(event) => {
          setEmail(event.target.value);
          feedback.edit('email');
        }}
        error={sentenceFor(feedback.refusals.email, refusals)}
      />
      <TextField
        label={RESET_COPY.code.code}
        name="code"
        mono
        autoComplete="one-time-code"
        autoCapitalize="characters"
        spellCheck={false}
        value={code}
        onChange={(event) => {
          setCode(event.target.value);
          feedback.edit('code');
        }}
        error={sentenceFor(feedback.refusals.code, refusals)}
      />
      <Button type="submit" full disabled={pending}>
        {pending ? RESET_COPY.code.submitting : RESET_COPY.code.submit}
      </Button>
      <div className={styles.links}>
        <p>
          {RESET_COPY.code.noEmail}{' '}
          <TextLink href="/forgot-password">{RESET_COPY.code.askAgain}</TextLink>
        </p>
        <TextLink href="/sign-in">{RESET_COPY.backToSignIn}</TextLink>
      </div>
    </Form>
  );
}
