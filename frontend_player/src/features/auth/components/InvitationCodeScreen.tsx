/**
 * ***Have an invitation code?*** — **the email the club invited and the 8-character code from its
 * email** ([#518](https://github.com/Rakieta02/Rakieta/issues/518), PRD #500 story 114), for the
 * phone the email's button cannot reach. Reached from under the Sign in button, with whatever the
 * sign-in box held.
 *
 * *Forgot password?*'s code screen, asking for an invitation's: the same two boxes, the code read
 * the server's way and its length checked first, and a right code buys a ticket and pushes *Set
 * your password* over this screen — so *back* from there finds both boxes as they were, and since a
 * claim is not a use, the same code buys another ticket if the first ran out.
 *
 * **The refusals.** A wrong code lands under the code box. Expired, used and locked are told only to
 * someone who typed the right code, each in its own sentence; an email that already has an account
 * is told to sign in and accept from there (story 121), and *Back to sign in* is under the button.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { Button } from '@/shared/ui';

import { useClaimInvitationCode } from '../hooks/useAuthActions';
import { invitationCodeSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthFields, AuthFrame } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import { bannerMessage, errorUnderField } from './authErrorMessage';
import { CodeField } from './CodeField';
import { EmailField } from './EmailField';
import { INVITATION_COPY, invitationErrorMessage } from './invitationPresentation';
import { INVITATION_ROUTES } from './invitationRoutes';

const COPY = INVITATION_COPY.code;

/** A refusal of the code, in the words for somebody who typed one. */
const codeRefusal = invitationErrorMessage('code');

export interface InvitationCodeScreenProps {
  /** What the sign-in box held, or nothing. */
  readonly email: string;
}

export function InvitationCodeScreen({ email: initialEmail }: InvitationCodeScreenProps) {
  const router = useRouter();
  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const claim = useClaimInvitationCode();

  const submit = () => {
    const result = validate(invitationCodeSchema, { email, code });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    const claimed = result.values;
    claim.mutate(claimed, {
      onSuccess: (ticket) =>
        router.push({
          pathname: INVITATION_ROUTES.password,
          params: { ticket, email: claimed.email },
        }),
    });
  };

  const errorFor = (field: string) => errorUnderField(field, fieldErrors, claim.error, codeRefusal);
  const banner = bannerMessage(claim.error, codeRefusal);

  return (
    <AuthFrame title={COPY.title} lead={COPY.lead}>
      {banner === undefined ? null : <AuthNotice message={banner} />}

      <AuthFields>
        <EmailField
          value={email}
          onChangeText={setEmail}
          error={errorFor('email')}
          returnKeyType="next"
          editable={!claim.isPending}
        />
        <CodeField
          label={COPY.label}
          value={code}
          onChangeText={setCode}
          error={errorFor('code')}
          onSubmitEditing={submit}
          editable={!claim.isPending}
        />
      </AuthFields>

      <Button
        label={COPY.continue}
        size="lg"
        busyLabel={COPY.checking}
        busy={claim.isPending}
        onPress={submit}
      />

      <AuthLink label={INVITATION_COPY.backToSignIn} onPress={() => router.dismissTo('/sign-in')} />
    </AuthFrame>
  );
}
