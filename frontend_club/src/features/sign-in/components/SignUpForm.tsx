'use client';

import { useActionState, useState } from 'react';

import { ClubDetailsFields } from '@/features/club-details/components/ClubDetailsFields';
import type { MapSettings } from '@/features/club-details/mappers';
import { EMPTY_DRAFT, type DetailsDraft } from '@/features/club-details/schemas';
import { Button } from '@/ui/Button';
import { Form } from '@/ui/Form';
import { blankForm, sentenceFor, sentencesFor } from '@/ui/forms';
import { Notice } from '@/ui/Notice';
import { TextField } from '@/ui/TextField';
import { TextLink } from '@/ui/TextLink';
import { useFormFeedback } from '@/ui/useFormFeedback';

import { signUp } from '../actions';
import { PASSWORD_RULE, SIGN_UP_COPY, SIGN_UP_REFUSALS } from '../copy';
import type { SignUpField } from '../schemas';

import styles from './forms.module.css';

/**
 * **Sign up** (#500 story 89): the club's name, district and city, the sports it offers, a pin on
 * the map, and the email and password the desk will sign in with. Every refusal lands under the
 * field it is about, whether this form or the backend made it.
 */
export function SignUpForm({ map }: { map: MapSettings }) {
  const [state, formAction, pending] = useActionState(signUp, blankForm<SignUpField>());
  const feedback = useFormFeedback(state);
  const [draft, setDraft] = useState<DetailsDraft>(EMPTY_DRAFT);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const sentences = sentencesFor(feedback.refusals, SIGN_UP_REFUSALS);
  const formSentence = sentenceFor(feedback.formRefusal, SIGN_UP_REFUSALS);

  return (
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
      <hr className={styles.rule} />
      <TextField
        label={SIGN_UP_COPY.email}
        name="email"
        type="email"
        autoComplete="username"
        hint={SIGN_UP_COPY.emailHint}
        value={email}
        onChange={(event) => {
          setEmail(event.target.value);
          feedback.edit('email');
        }}
        error={sentences.email}
      />
      <TextField
        label={SIGN_UP_COPY.password}
        name="password"
        type="password"
        autoComplete="new-password"
        // The rule stands under the box until it is the refusal, and then it is said in red.
        hint={sentences.password === undefined ? PASSWORD_RULE : undefined}
        value={password}
        onChange={(event) => {
          setPassword(event.target.value);
          feedback.edit('password');
        }}
        error={sentences.password}
      />
      <Button type="submit" full disabled={pending}>
        {pending ? SIGN_UP_COPY.submitting : SIGN_UP_COPY.submit}
      </Button>
      <div className={styles.links}>
        <p>
          {SIGN_UP_COPY.haveAccount} <TextLink href="/sign-in">{SIGN_UP_COPY.signIn}</TextLink>
        </p>
      </div>
    </Form>
  );
}
