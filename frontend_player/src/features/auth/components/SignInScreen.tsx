/**
 * Sign in.
 *
 * The screen owns rendering and interaction. It owns no rule: what a valid email looks
 * like is `schemas/`, what signing in does is `use-cases/`, and what a failure means is
 * the error model. A `disabled={…}` expression encoding a rule would be a rule nobody
 * can test.
 *
 * **The password box can be read back**, exactly as both of the sign-up form's can. The
 * argument there was a typo nobody can see costing a player the whole form; here it is a
 * typo nobody can see costing them a refusal they cannot distinguish from a wrong password
 * — and a keychain that filled the box with the wrong entry looks identical either way. One
 * box, so the control's accessible name still says which field it is about and there is
 * nothing for it to be confused with.
 *
 * **Its pieces are the recovery screens' pieces** — the frame, the email box, the text link
 * ([#515](https://github.com/Raketa02/Raketa/issues/515)). ***Forgot password?*** sits under the
 * Sign in button, on the one sign-in screen players and administrators share, and carries what
 * is in the email box across so it is not typed twice. ***Have an invitation code?*** sits under
 * it ([#518](https://github.com/Raketa02/Raketa/issues/518)), for somebody a club invited whose
 * phone the email's button cannot reach, and carries the email the same way.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { Button, TextField } from '@/shared/ui';

import { useSignIn } from '../hooks/useAuthActions';
import { signInSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthFields, AuthFrame } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import { PASSWORD_LABEL, SIGN_IN_COPY } from './authPresentation';
import { authErrorMessage } from './authErrorMessage';
import { EmailField } from './EmailField';
import { INVITATION_COPY } from './invitationPresentation';
import { invitationCodeHref } from './invitationRoutes';
import { RESET_COPY } from './resetPresentation';
import { askForResetHref } from './resetRoutes';

export function SignInScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const signIn = useSignIn();

  const submit = () => {
    const result = validate(signInSchema, { email, password });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    signIn.mutate(result.values);
  };

  const forgotPassword = () => router.push(askForResetHref(email));
  const haveACode = () => router.push(invitationCodeHref(email));

  return (
    <AuthFrame title={SIGN_IN_COPY.title}>
      {signIn.error !== null ? <AuthNotice message={authErrorMessage(signIn.error)} /> : null}

      <AuthFields>
        <EmailField
          value={email}
          onChangeText={setEmail}
          error={fieldErrors.email}
          returnKeyType="next"
          editable={!signIn.isPending}
        />
        <TextField
          label={PASSWORD_LABEL}
          value={password}
          onChangeText={setPassword}
          error={fieldErrors.password}
          secureTextEntry
          reveal
          autoCapitalize="none"
          autoComplete="current-password"
          textContentType="password"
          returnKeyType="go"
          onSubmitEditing={submit}
          editable={!signIn.isPending}
        />
      </AuthFields>

      <Button
        label={SIGN_IN_COPY.submit}
        size="lg"
        busyLabel={SIGN_IN_COPY.submitting}
        busy={signIn.isPending}
        onPress={submit}
      />

      <AuthLink label={RESET_COPY.signInLink} onPress={forgotPassword} />

      <AuthLink label={INVITATION_COPY.signInLink} onPress={haveACode} />

      <AuthLink lead={SIGN_IN_COPY.newHere} label={SIGN_IN_COPY.createAccount} href="/sign-up" />
    </AuthFrame>
  );
}
