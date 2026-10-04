/**
 * **The emailed code's box** — the props that make a box the one an 8-character code is typed into,
 * `EmailField`'s reason for existing: *Enter the code* (#515) and *Have an invitation code?* (#518)
 * each ask for one, and the one machinery sends both.
 *
 * Upper case is how the code is written and read aloud, so the keyboard offers it; the server
 * forgives either, and the schema reads it the server's way. Nothing is corrected, and the platform
 * may fill it from the message it arrived in.
 */

import { TextField, type TextFieldProps } from '@/shared/ui';

export type CodeFieldProps = Omit<
  TextFieldProps,
  'autoCapitalize' | 'autoCorrect' | 'autoComplete' | 'textContentType' | 'returnKeyType'
>;

export function CodeField(props: CodeFieldProps) {
  return (
    <TextField
      autoCapitalize="characters"
      autoCorrect={false}
      autoComplete="one-time-code"
      textContentType="oneTimeCode"
      returnKeyType="go"
      {...props}
    />
  );
}
