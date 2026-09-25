/**
 * **Choosing a password: the box, the repeat, and the rule** — sign-up's two boxes, and *Set a
 * new password*'s ([#515](https://github.com/Raketa02/Raketa/issues/515)).
 *
 * **Both boxes can be read back.** These are the forms that ask for the same secret twice and
 * refuse on a mismatch, so a typo nobody can see costs the whole form — and, on a phone whose
 * keychain filled one box and not the other, makes it impossible to tell what happened. Each box
 * reveals on its own; showing one says nothing about the other.
 *
 * **The rule is written under the first box before anything is typed**, the naming's shape for
 * the nickname's: a refusal should never be the first a person hears of a rule. It reaches a
 * listener as the box's hint, and it is not drawn twice — when the box is refused, the refusal
 * line has the sentence.
 */

import { StyleSheet, Text, View } from 'react-native';

import { TextField, theme } from '@/shared/ui';

import { PASSWORD_RULE } from '../schemas/authForms';

import { REPEAT_PASSWORD_LABEL } from './authPresentation';

export interface PasswordPairFieldsProps {
  /** The first box's label — *Password* on sign-up, *New password* on a reset. */
  readonly label: string;
  readonly password: string;
  readonly onChangePassword: (typed: string) => void;
  readonly passwordError: string | undefined;
  readonly repeat: string;
  readonly onChangeRepeat: (typed: string) => void;
  readonly repeatError: string | undefined;
  /** The repeat box's *go* — the form's submit. */
  readonly onSubmitEditing: () => void;
  readonly editable: boolean;
}

export function PasswordPairFields({
  label,
  password,
  onChangePassword,
  passwordError,
  repeat,
  onChangeRepeat,
  repeatError,
  onSubmitEditing,
  editable,
}: PasswordPairFieldsProps) {
  return (
    <>
      <View style={s.box}>
        <TextField
          label={label}
          value={password}
          onChangeText={onChangePassword}
          error={passwordError}
          accessibilityHint={PASSWORD_RULE}
          secureTextEntry
          reveal
          autoCapitalize="none"
          autoComplete="new-password"
          textContentType="newPassword"
          editable={editable}
        />
        {passwordError === undefined ? <Text style={s.rule}>{PASSWORD_RULE}</Text> : null}
      </View>
      <TextField
        label={REPEAT_PASSWORD_LABEL}
        value={repeat}
        onChangeText={onChangeRepeat}
        error={repeatError}
        secureTextEntry
        reveal
        autoCapitalize="none"
        autoComplete="new-password"
        textContentType="newPassword"
        returnKeyType="go"
        onSubmitEditing={onSubmitEditing}
        editable={editable}
      />
    </>
  );
}

const s = StyleSheet.create({
  box: { gap: theme.space.xxs },
  rule: { ...theme.type.tiny, color: theme.color.muted },
});
