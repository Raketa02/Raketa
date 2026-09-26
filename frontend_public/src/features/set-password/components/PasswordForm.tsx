'use client';

import { useActionState, useState } from 'react';

import { blankForm, sentenceFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { CardSection } from '@/ui/PageCard';
import { SubmitButton } from '@/ui/SubmitButton';
import { TextField } from '@/ui/TextField';
import { useFormFeedback } from '@/ui/useFormFeedback';

import {
  NEEDS_JAVASCRIPT,
  PASSWORD_REFUSALS,
  PASSWORD_RULE,
  type PasswordFormWords,
} from '../copy';
import type { PasswordField, PasswordFormState } from '../schemas';

import styles from './PasswordForm.module.css';

type Action = (previous: PasswordFormState, form: FormData) => Promise<PasswordFormState>;

/**
 * **Choose a password, twice**, for a link's page. A refusal goes under the box it is about, or
 * over the form when it is about neither (an account already there, the backend unreachable).
 * The boxes are controlled, so a refusal keeps what was typed.
 *
 * **It needs JavaScript**: under `Referrer-Policy: no-referrer` a browser posts a plain form with
 * `Origin: null`, which Next refuses as a cross-site action. A browser without it is told so.
 *
 * `refusals` are the page's own sentences, beside the rule's.
 */
export function PasswordForm({
  action,
  words,
  refusals,
}: {
  action: Action;
  words: PasswordFormWords;
  refusals: Readonly<Record<string, string>>;
}) {
  const [state, formAction, pending] = useActionState(action, blankForm<PasswordField>());
  const feedback = useFormFeedback(state);
  const [password, setPassword] = useState('');
  const [repeat, setRepeat] = useState('');
  const table = { ...PASSWORD_REFUSALS, ...refusals };
  const formSentence = sentenceFor(feedback.formRefusal, table);
  const passwordSentence = sentenceFor(feedback.refusals.password, table);

  return (
    <CardSection>
      <form action={formAction} noValidate className={styles.form}>
        {words.title === undefined ? null : <h2 className={styles.title}>{words.title}</h2>}
        {words.lead === undefined ? null : <p className={styles.lead}>{words.lead}</p>}
        <noscript>
          <Notice tone="info">{NEEDS_JAVASCRIPT}</Notice>
        </noscript>
        {formSentence === null ? null : <Notice tone="error">{formSentence}</Notice>}
        <TextField
          label={words.password}
          name="password"
          type="password"
          autoComplete="new-password"
          hint={passwordSentence === null ? PASSWORD_RULE : undefined}
          error={passwordSentence}
          value={password}
          onChange={(event) => {
            setPassword(event.target.value);
            feedback.edit('password');
          }}
        />
        <TextField
          label={words.repeat}
          name="repeat"
          type="password"
          autoComplete="new-password"
          error={sentenceFor(feedback.refusals.repeat, table)}
          value={repeat}
          onChange={(event) => {
            setRepeat(event.target.value);
            feedback.edit('repeat');
          }}
        />
        <SubmitButton pending={pending}>{pending ? words.submitting : words.submit}</SubmitButton>
      </form>
    </CardSection>
  );
}
