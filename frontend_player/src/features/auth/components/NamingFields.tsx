/**
 * The naming's one box — **the control, without the screen around it.**
 *
 * A **Nickname** under its label, and each refusal under it
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). The
 * naming step draws it empty under *How should people see you?*; the You tab's *Nickname* draws
 * it pre-filled under a *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7). What is typed, what is refused and what is sent are `useNamingForm`'s; what is here is
 * the drawing, once, so a rule retuned on the step is retuned on the tab in the same commit.
 *
 * **No hint under the box.** The handle's rule — *Use letters, numbers, and . _ - only — no
 * spaces.* — is drawn only as the box's error, when what was typed breaks it: the schema's own
 * refusal carries the sentence, and the many who never break it read one field and nothing else.
 *
 * **The banner is drawn here too**, above the box, because it belongs to the form and not to
 * either screen: a refusal against no field is the form's, wherever the form is.
 */

import { StyleSheet, View } from 'react-native';

import { TextField, theme } from '@/shared/ui';

import type { NamingForm } from '../hooks/useNamingForm';

import { AuthNotice } from './AuthNotice';
import { bannerMessage, errorUnderField } from './authErrorMessage';
import { NICKNAME_LABEL } from './namingPresentation';

export interface NamingFieldsProps {
  readonly form: NamingForm;
}

export function NamingFields({ form }: NamingFieldsProps) {
  // A conflict the server raised against the box belongs under it. Anything else stays in the
  // banner.
  const nicknameError = errorUnderField('nickname', form.fieldErrors, form.error);
  const banner = bannerMessage(form.error);

  return (
    <>
      {banner === undefined ? null : <AuthNotice message={banner} />}

      <View style={s.form}>
        <TextField
          label={NICKNAME_LABEL}
          value={form.nickname}
          onChangeText={form.setNickname}
          error={nicknameError}
          autoCapitalize="none"
          autoCorrect={false}
          textContentType="nickname"
          returnKeyType="go"
          onSubmitEditing={form.submit}
          editable={!form.pending}
        />
      </View>
    </>
  );
}

const s = StyleSheet.create({
  form: { gap: theme.space.md },
});
