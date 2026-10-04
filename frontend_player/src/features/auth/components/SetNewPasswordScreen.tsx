/**
 * ***Set a new password*** — by a claimed code, or by the email's link
 * ([#515](https://github.com/Raketa02/Raketa/issues/515),
 * [ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §5).
 *
 * The one password rule and a repeat, sign-up's own two boxes. Setting it **signs out
 * everywhere and signs this session in** (ADR-0185 §7), which the lead says before the press: a
 * person whose other phone goes quiet should have been told why. The screen does not navigate on
 * success — the `(auth)` guard sees the session begin and hands it to the entry gate, which knows
 * where this account belongs — and the toast is the *done*.
 *
 * **The two ways in differ in one thing: where to go when it did not work** (`resetWayOut`). A
 * ticket runs out after fifteen minutes and the code screen under this one still holds the code,
 * which buys another, so the way out is back to it — until a refusal says the email itself is
 * spent, when it is *Ask again* with the address carried. A link has no screen under it, so its way
 * out is always asking again. The refusals are worded by the same difference — *that code* and
 * *that link* — in `resetPresentation`.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { Button } from '@/shared/ui';

import type { ResetKey } from '../domain/passwordReset';
import { useSetNewPassword } from '../hooks/useAuthActions';
import { newPasswordSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthFields, AuthFrame } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import { bannerMessage, errorUnderField } from './authErrorMessage';
import { PasswordPairFields } from './PasswordPairFields';
import { RESET_COPY, resetErrorMessage, resetWayOut } from './resetPresentation';
import { RESET_ROUTES, askForResetHref } from './resetRoutes';

export interface SetNewPasswordScreenProps {
  readonly resetKey: ResetKey;
  /** The address a claimed code was sent to, for *Ask again*; nothing by a link. */
  readonly email: string;
}

export function SetNewPasswordScreen({ resetKey, email }: SetNewPasswordScreenProps) {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const setNew = useSetNewPassword({ done: RESET_COPY.done });
  const refusal = resetErrorMessage(resetKey.via);

  const submit = () => {
    const result = validate(newPasswordSchema, { password, confirmPassword });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    setNew.mutate({ key: resetKey, password: result.values.password });
  };

  const errorFor = (field: string) => errorUnderField(field, fieldErrors, setNew.error, refusal);
  const banner = bannerMessage(setNew.error, refusal);

  return (
    <AuthFrame title={RESET_COPY.newPassword.title} lead={RESET_COPY.newPassword.lead}>
      {banner === undefined ? null : <AuthNotice message={banner} />}

      <AuthFields>
        <PasswordPairFields
          label={RESET_COPY.newPassword.label}
          password={password}
          onChangePassword={setPassword}
          passwordError={errorFor('password')}
          repeat={confirmPassword}
          onChangeRepeat={setConfirmPassword}
          repeatError={errorFor('confirmPassword')}
          onSubmitEditing={submit}
          editable={!setNew.isPending}
        />
      </AuthFields>

      <Button
        label={RESET_COPY.newPassword.set}
        size="lg"
        busyLabel={RESET_COPY.newPassword.setting}
        busy={setNew.isPending}
        onPress={submit}
      />

      {resetWayOut(resetKey.via, setNew.error) === 'code' ? (
        <AuthLink
          label={RESET_COPY.newPassword.enterCodeAgain}
          // The code screen is under this one whenever a ticket exists; a route opened any other
          // way has nothing under it, and the code screen is where a ticket comes from.
          onPress={() => (router.canGoBack() ? router.back() : router.replace(RESET_ROUTES.code))}
        />
      ) : (
        <AuthLink
          lead={resetKey.via === 'link' ? RESET_COPY.newPassword.linkTrouble : undefined}
          label={RESET_COPY.newPassword.askAgain}
          onPress={() => router.push(askForResetHref(email))}
        />
      )}
    </AuthFrame>
  );
}
