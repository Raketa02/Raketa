'use client';

import { useActionState, useState } from 'react';

import { Button, ButtonLink } from '@/ui/Button';
import { Form } from '@/ui/Form';
import { sentenceFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { TextField } from '@/ui/TextField';
import { TextLink } from '@/ui/TextLink';
import { useFormFeedback } from '@/ui/useFormFeedback';

import { askForReset, type AskState } from '../actions';
import { AUTH_REFUSALS, RESET_COPY } from '../copy';

import styles from './forms.module.css';

const NOTHING_YET: AskState = { refusals: {}, formRefusal: null, sentTo: null };

/**
 * **Forgot password?** (#500 story 91): the club's email, then one sentence for everybody. The
 * sentence cannot say whether the address signs a club in, because the backend does not say
 * either (ADR-0184 §5).
 */
export function ForgotPasswordForm({ email: offered }: { email: string }) {
  const [state, formAction, pending] = useActionState(askForReset, NOTHING_YET);
  const feedback = useFormFeedback(state);
  const [email, setEmail] = useState(offered);

  if (state.sentTo !== null) {
    return (
      <div className={styles.form}>
        <h2 className={styles.heading}>{RESET_COPY.sent.title}</h2>
        <p role="status">{RESET_COPY.sent.lead(state.sentTo)}</p>
        <ButtonLink href="/forgot-password/code" tone="primary">
          {RESET_COPY.sent.enterCode}
        </ButtonLink>
        <div className={styles.links}>
          <TextLink href="/sign-in">{RESET_COPY.backToSignIn}</TextLink>
        </div>
      </div>
    );
  }

  const formSentence = sentenceFor(feedback.formRefusal, AUTH_REFUSALS);
  return (
    <Form action={formAction} className={styles.form}>
      <h2 className={styles.heading}>{RESET_COPY.ask.title}</h2>
      <p className={styles.lead}>{RESET_COPY.ask.lead}</p>
      {formSentence === null ? null : <Notice tone="error">{formSentence}</Notice>}
      <TextField
        label={RESET_COPY.ask.email}
        name="email"
        type="email"
        autoComplete="username"
        value={email}
        onChange={(event) => {
          setEmail(event.target.value);
          feedback.edit('email');
        }}
        error={sentenceFor(feedback.refusals.email, AUTH_REFUSALS)}
      />
      <Button type="submit" full disabled={pending}>
        {pending ? RESET_COPY.ask.sending : RESET_COPY.ask.send}
      </Button>
      <div className={styles.links}>
        <TextLink href="/sign-in">{RESET_COPY.backToSignIn}</TextLink>
      </div>
    </Form>
  );
}
