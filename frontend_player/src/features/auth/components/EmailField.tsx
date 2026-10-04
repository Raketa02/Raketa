/**
 * **The email box every auth form opens with** — sign-in, sign-up, *Forgot password?* and the
 * code screen. What makes it an email box is five props that were copied onto each: no capitals,
 * no correction, the email keyboard, and both platforms' autofill hints (6.13 — neither reads the
 * other's). One place for them, so a fifth form cannot forget one.
 *
 * `textContentType` stays the caller's, and it is the one that differs: `username` wherever a
 * password is about to be typed or recovered, so iOS offers the saved account; `emailAddress` on
 * sign-up, where there is no saved account yet.
 */

import { TextField, type TextFieldProps } from '@/shared/ui';

import { EMAIL_LABEL } from './authPresentation';

export type EmailFieldProps = Omit<
  TextFieldProps,
  'label' | 'autoCapitalize' | 'autoComplete' | 'autoCorrect' | 'keyboardType' | 'textContentType'
> & {
  readonly textContentType?: 'username' | 'emailAddress';
};

export function EmailField({ textContentType = 'username', ...props }: EmailFieldProps) {
  return (
    <TextField
      label={EMAIL_LABEL}
      autoCapitalize="none"
      autoComplete="email"
      autoCorrect={false}
      keyboardType="email-address"
      textContentType={textContentType}
      {...props}
    />
  );
}
