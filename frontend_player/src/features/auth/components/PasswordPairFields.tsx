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
 *
 * **`stage` is sign-up's on the stage** ([#785](https://github.com/Raketa02/Raketa/issues/785),
 * mocks 4 and 6): both boxes in the shared field's `stage` look, each refusal on its box's label
 * row (`errorOnLabelRow`), the placeholders *At least 8 characters* and *Once more* — and **the rule
 * under the first box all the time**. The refusal has moved up to the label row, so nothing is said
 * twice in one place and the rule no longer has to give way: the form does not shift under a press,
 * and the sentence a refusal points at stays beside it. *Set a new password* and *Set your password*
 * keep today's frame and today's shape.
 */

import { StyleSheet, Text, View } from 'react-native';

import { TextField, theme } from '@/shared/ui';

import { PASSWORD_RULE } from '../schemas/authForms';

import {
  PASSWORD_PLACEHOLDER,
  REPEAT_PASSWORD_LABEL,
  REPEAT_PASSWORD_PLACEHOLDER,
} from './authPresentation';

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
  /** Sign-up on the stage — the look, the label-row refusals, the placeholders, the rule kept. */
  readonly stage?: boolean;
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
  stage = false,
}: PasswordPairFieldsProps) {
  // On the stage a refusal is drawn on the label's row, so the rule under the box never gives way.
  const ruleShown = stage || passwordError === undefined;

  return (
    <>
      <View style={s.box}>
        <TextField
          label={label}
          value={password}
          onChangeText={onChangePassword}
          error={passwordError}
          stage={stage}
          errorOnLabelRow={stage}
          placeholder={stage ? PASSWORD_PLACEHOLDER : undefined}
          accessibilityHint={PASSWORD_RULE}
          secureTextEntry
          reveal
          autoCapitalize="none"
          autoComplete="new-password"
          textContentType="newPassword"
          editable={editable}
        />
        {ruleShown ? <Text style={s.rule}>{PASSWORD_RULE}</Text> : null}
      </View>
      <TextField
        label={REPEAT_PASSWORD_LABEL}
        value={repeat}
        onChangeText={onChangeRepeat}
        error={repeatError}
        stage={stage}
        errorOnLabelRow={stage}
        placeholder={stage ? REPEAT_PASSWORD_PLACEHOLDER : undefined}
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
