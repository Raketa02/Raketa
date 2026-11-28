/**
 * ***Set your password*** — an invited person choosing the password they will sign in with, **their
 * email locked** ([#518](https://github.com/Rakieta02/Rakieta/issues/518), PRD #500 stories 113–116,
 * [ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §2).
 *
 * *Set a new password*'s form under the invitation's words: the one password rule and a repeat,
 * sign-up's own two boxes — and above them **the email, drawn in its box and not editable**, because
 * the club invited that address and the account the password opens is that address's. Setting it
 * creates the account (or gives back a password the club reset) and **signs this session in**; the
 * screen does not navigate — the `(auth)` guard hands the session to the entry gate, which opens the
 * administrator area of an account that only administers (ADR-0185 §3).
 *
 * **The two ways in differ in where to go when it did not work** (`invitationWayOut`). A ticket runs
 * out after a few minutes and the code screen under this one still holds the code, which buys
 * another, so the way out is back to it — until a refusal says the invitation itself is spent, when
 * it is *Back to sign in*. A link has no screen under it, so its way out is always sign in.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { Button } from '@/shared/ui';

import type { InvitationKey } from '../domain/invitation';
import { useSetInvitationPassword } from '../hooks/useAuthActions';
import { newPasswordSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthFields, AuthFrame } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import { bannerMessage, errorUnderField } from './authErrorMessage';
import { EmailField } from './EmailField';
import {
  INVITATION_COPY,
  invitationErrorMessage,
  invitationWayOut,
} from './invitationPresentation';
import { INVITATION_ROUTES } from './invitationRoutes';
import { PasswordPairFields } from './PasswordPairFields';

const COPY = INVITATION_COPY.password;

export interface SetYourPasswordScreenProps {
  readonly invitationKey: InvitationKey;
  /** The address the invitation is to — the code's, or the link's as the server read it. */
  readonly email: string;
}

export function SetYourPasswordScreen({ invitationKey, email }: SetYourPasswordScreenProps) {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const set = useSetInvitationPassword();
  const refusal = invitationErrorMessage(invitationKey.via);

  const submit = () => {
    const result = validate(newPasswordSchema, { password, confirmPassword });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    set.mutate({ key: invitationKey, password: result.values.password });
  };

  const errorFor = (field: string) => errorUnderField(field, fieldErrors, set.error, refusal);
  const banner = bannerMessage(set.error, refusal);

  return (
    <AuthFrame title={COPY.title} lead={COPY.lead}>
      {banner === undefined ? null : <AuthNotice message={banner} />}

      <AuthFields>
        {/* Drawn as a box so it reads as the account's address, and locked: the invitation is to
            it. `textContentType` is the username's, so a password manager files the new password
            under the right account. */}
        <EmailField value={email} editable={false} />
        <PasswordPairFields
          label={COPY.label}
          password={password}
          onChangePassword={setPassword}
          passwordError={errorFor('password')}
          repeat={confirmPassword}
          onChangeRepeat={setConfirmPassword}
          repeatError={errorFor('confirmPassword')}
          onSubmitEditing={submit}
          editable={!set.isPending}
        />
      </AuthFields>

      <Button
        label={COPY.set}
        size="lg"
        busyLabel={COPY.setting}
        busy={set.isPending}
        onPress={submit}
      />

      {invitationWayOut(invitationKey.via, set.error) === 'code' ? (
        <AuthLink
          label={COPY.enterCodeAgain}
          // The code screen is under this one whenever a ticket exists; a route opened any other
          // way has nothing under it, and the code screen is where a ticket comes from.
          onPress={() =>
            router.canGoBack() ? router.back() : router.replace(INVITATION_ROUTES.code)
          }
        />
      ) : (
        <AuthLink
          label={INVITATION_COPY.backToSignIn}
          onPress={() => router.dismissTo('/sign-in')}
        />
      )}
    </AuthFrame>
  );
}
