/**
 * *Enter the code* — **the email and the 8-character code**
 * ([#515](https://github.com/Rakieta02/Rakieta/issues/515)), for the phone the email's button
 * cannot reach: the email was opened on a laptop, or the link would not open the app.
 *
 * Both boxes, because the server exchanges the pair and not the code alone; the email opens with
 * the address the confirmation was about. A right code buys a ticket and *Set a new password*
 * is pushed over this screen, so *back* from there finds both boxes as they were — and since a
 * claim is not a use, the same code buys another ticket if the first ran out.
 *
 * **The refusals.** A wrong code lands under the code box: it is the one the person has to change,
 * and the server says it for a wrong code and for an address nothing was sent to alike. Expired,
 * used and locked are told only to someone who typed the right code, and each is its own sentence
 * in the banner; the expired one says to ask again, and *Ask again* is under the button.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { Button } from '@/shared/ui';

import { useClaimResetCode } from '../hooks/useAuthActions';
import { resetCodeSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthFields, AuthFrame } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import { bannerMessage, errorUnderField } from './authErrorMessage';
import { CodeField } from './CodeField';
import { EmailField } from './EmailField';
import { RESET_COPY, resetErrorMessage } from './resetPresentation';
import { RESET_ROUTES, askForResetHref } from './resetRoutes';

/** A refusal of the code, in the words for somebody who typed one. */
const codeRefusal = resetErrorMessage('code');

export interface ResetCodeScreenProps {
  /** The address the confirmation was about, or nothing. */
  readonly email: string;
}

export function ResetCodeScreen({ email: initialEmail }: ResetCodeScreenProps) {
  const router = useRouter();
  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const claim = useClaimResetCode();

  const submit = () => {
    const result = validate(resetCodeSchema, { email, code });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    const claimed = result.values;
    claim.mutate(claimed, {
      onSuccess: (ticket) =>
        router.push({
          pathname: RESET_ROUTES.newPassword,
          params: { ticket, email: claimed.email },
        }),
    });
  };

  const errorFor = (field: string) => errorUnderField(field, fieldErrors, claim.error, codeRefusal);
  const banner = bannerMessage(claim.error, codeRefusal);

  return (
    <AuthFrame title={RESET_COPY.code.title} lead={RESET_COPY.code.lead}>
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
          label={RESET_COPY.code.label}
          value={code}
          onChangeText={setCode}
          error={errorFor('code')}
          onSubmitEditing={submit}
          editable={!claim.isPending}
        />
      </AuthFields>

      <Button
        label={RESET_COPY.code.continue}
        size="lg"
        busyLabel={RESET_COPY.code.checking}
        busy={claim.isPending}
        onPress={submit}
      />

      <AuthLink
        lead={RESET_COPY.code.noEmail}
        label={RESET_COPY.code.askAgain}
        onPress={() => router.push(askForResetHref(email))}
      />
    </AuthFrame>
  );
}
