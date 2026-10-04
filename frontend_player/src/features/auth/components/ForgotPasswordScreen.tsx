/**
 * *Forgot password?* — **the email to send a link and a code to**
 * ([#515](https://github.com/Raketa02/Raketa/issues/515)).
 *
 * The sign-in screen's pieces asking one thing. Opened from under the Sign in button with what
 * was typed there already in the box, and from the code screen's *Ask again* the same way.
 *
 * **Whatever the server does with it, the next screen is the same one.** The answer is `202` for
 * an address with an account, without one, and past the throttle, so the only failure this form
 * can show is one about reaching the server — never one about the address.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { Button } from '@/shared/ui';

import { useAskForPasswordReset } from '../hooks/useAuthActions';
import { forgotPasswordSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthFields, AuthFrame } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import { authErrorMessage } from './authErrorMessage';
import { EmailField } from './EmailField';
import { RESET_COPY } from './resetPresentation';
import { RESET_ROUTES } from './resetRoutes';

export interface ForgotPasswordScreenProps {
  /** What the box opens with — the sign-in screen's, or the code screen's on *Ask again*. */
  readonly email: string;
}

export function ForgotPasswordScreen({ email: initialEmail }: ForgotPasswordScreenProps) {
  const router = useRouter();
  const [email, setEmail] = useState(initialEmail);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const ask = useAskForPasswordReset();

  const submit = () => {
    const result = validate(forgotPasswordSchema, { email });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    const asked = result.values.email;
    ask.mutate(asked, {
      onSuccess: () => router.push({ pathname: RESET_ROUTES.sent, params: { email: asked } }),
    });
  };

  return (
    <AuthFrame title={RESET_COPY.ask.title} lead={RESET_COPY.ask.lead}>
      {ask.error === null ? null : <AuthNotice message={authErrorMessage(ask.error)} />}

      <AuthFields>
        <EmailField
          value={email}
          onChangeText={setEmail}
          error={fieldErrors.email}
          returnKeyType="send"
          onSubmitEditing={submit}
          editable={!ask.isPending}
        />
      </AuthFields>

      <Button
        label={RESET_COPY.ask.send}
        size="lg"
        busyLabel={RESET_COPY.ask.sending}
        busy={ask.isPending}
        onPress={submit}
      />

      <AuthLink label={RESET_COPY.backToSignIn} onPress={() => router.dismissTo('/sign-in')} />
    </AuthFrame>
  );
}
