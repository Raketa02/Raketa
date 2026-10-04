'use client';

import { useActionState, useState } from 'react';

import { Button } from '@/ui/Button';
import { Form } from '@/ui/Form';
import { blankForm, sentenceFor, type FormState } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { TextField } from '@/ui/TextField';
import { TextLink } from '@/ui/TextLink';
import { useFormFeedback } from '@/ui/useFormFeedback';

import { PASSWORD_RULE, RESET_COPY, RESET_REFUSALS, resetWayOut, type ResetVia } from '../copy';
import type { NewPasswordField } from '../schemas';

import styles from './forms.module.css';

type Action = (
  previous: FormState<NewPasswordField>,
  form: FormData,
) => Promise<FormState<NewPasswordField>>;

/**
 * **Set a new password**, reached by a claimed code or by the email's link. Setting it signs
 * this browser in and every other one out. **The way out follows the refusal**: back to the code
 * while it can still buy a ticket, otherwise *Ask again*; by a link, always *Ask again*.
 */
export function NewPasswordForm({ via, action }: { via: ResetVia; action: Action }) {
  const [state, formAction, pending] = useActionState(action, blankForm<NewPasswordField>());
  const feedback = useFormFeedback(state);
  const [password, setPassword] = useState('');
  const refusals = RESET_REFUSALS[via];
  const formSentence = sentenceFor(feedback.formRefusal, refusals);
  const passwordSentence = sentenceFor(feedback.refusals.password, refusals);
  const wayOut = resetWayOut(via, state.formRefusal);

  return (
    <Form action={formAction} className={styles.form}>
      <h2 className={styles.heading}>{RESET_COPY.newPassword.title}</h2>
      <p className={styles.lead}>{RESET_COPY.newPassword.lead}</p>
      {formSentence === null ? null : <Notice tone="error">{formSentence}</Notice>}
      <TextField
        label={RESET_COPY.newPassword.password}
        name="password"
        type="password"
        autoComplete="new-password"
        hint={passwordSentence === null ? PASSWORD_RULE : undefined}
        value={password}
        onChange={(event) => {
          setPassword(event.target.value);
          feedback.edit('password');
        }}
        error={passwordSentence}
      />
      <Button type="submit" full disabled={pending}>
        {pending ? RESET_COPY.newPassword.submitting : RESET_COPY.newPassword.submit}
      </Button>
      <div className={styles.links}>
        {wayOut === 'code' ? (
          <TextLink href="/forgot-password/code">{RESET_COPY.newPassword.enterCodeAgain}</TextLink>
        ) : (
          <p>
            {via === 'link' ? `${RESET_COPY.newPassword.linkTrouble} ` : null}
            <TextLink href="/forgot-password">{RESET_COPY.newPassword.askAgain}</TextLink>
          </p>
        )}
        <TextLink href="/sign-in">{RESET_COPY.backToSignIn}</TextLink>
      </div>
    </Form>
  );
}
