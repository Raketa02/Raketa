'use client';

import { useActionState, useState } from 'react';

import { Button } from '@/ui/Button';
import { Form } from '@/ui/Form';
import { blankForm, sentenceFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { TextField } from '@/ui/TextField';
import { TextLink } from '@/ui/TextLink';
import { useFormFeedback } from '@/ui/useFormFeedback';

import { signIn } from '../actions';
import { AUTH_REFUSALS, SIGN_IN_COPY, type SignInNotice } from '../copy';
import type { SignInField } from '../schemas';

import styles from './forms.module.css';

/**
 * **Sign in** (club mock 1): CLUB EMAIL, PASSWORD and **Sign in**, then the ways to *Forgot
 * password?* and to signing up. `notice` says why the desk is here: a session that ended, one
 * that could not be renewed, or a sign-up whose sign-in did not follow.
 */
export function SignInForm({ notice }: { notice: SignInNotice | null }) {
  const [state, formAction, pending] = useActionState(signIn, blankForm<SignInField>());
  const feedback = useFormFeedback(state);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const formSentence = sentenceFor(feedback.formRefusal, AUTH_REFUSALS);

  return (
    <Form action={formAction} className={styles.form}>
      {notice !== null && !feedback.touched && state.formRefusal === null ? (
        <Notice tone="info">{SIGN_IN_COPY.notices[notice]}</Notice>
      ) : null}
      {formSentence === null ? null : <Notice tone="error">{formSentence}</Notice>}
      <TextField
        label={SIGN_IN_COPY.email}
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
      <TextField
        label={SIGN_IN_COPY.password}
        name="password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(event) => {
          setPassword(event.target.value);
          feedback.edit('password');
        }}
        error={sentenceFor(feedback.refusals.password, AUTH_REFUSALS)}
      />
      <Button type="submit" full disabled={pending}>
        {pending ? SIGN_IN_COPY.submitting : SIGN_IN_COPY.submit}
      </Button>
      <div className={styles.links}>
        <TextLink href="/forgot-password">{SIGN_IN_COPY.forgot}</TextLink>
        <p>
          {SIGN_IN_COPY.newClub} <TextLink href="/sign-up">{SIGN_IN_COPY.signUp}</TextLink>
        </p>
      </div>
    </Form>
  );
}
