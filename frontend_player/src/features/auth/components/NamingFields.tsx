/**
 * The naming's two boxes — **the control, without the screen around it.**
 *
 * A **Name** and a **Nickname** under their labels, the handle's rule under its box before
 * anything is typed, and each refusal under the box it names
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §1). The naming step draws them empty under *How should people see you?*; the You tab's
 * *Name* draws them pre-filled under a *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7). What is typed, what is refused and what is sent are `useNamingForm`'s; what is here is
 * the drawing, once, so a rule retuned on the step is retuned on the tab in the same commit.
 *
 * **The banner is drawn here too**, above the boxes, because it belongs to the form and not to
 * either screen: a refusal against no field is the form's, wherever the form is.
 */

import { StyleSheet, Text, View } from 'react-native';

import { TextField, theme } from '@/shared/ui';

import type { NamingForm } from '../hooks/useNamingForm';
import { NICKNAME_RULE } from '../schemas/authForms';

import { AuthNotice } from './AuthNotice';
import { bannerMessage, errorUnderField } from './authErrorMessage';
import { NAME_LABEL, NICKNAME_LABEL } from './namingPresentation';

export interface NamingFieldsProps {
  readonly form: NamingForm;
}

export function NamingFields({ form }: NamingFieldsProps) {
  // A conflict the server raised against one field belongs under that field. Anything else
  // stays in the banner.
  const nameError = errorUnderField('name', form.fieldErrors, form.error);
  const nicknameError = errorUnderField('nickname', form.fieldErrors, form.error);
  const banner = bannerMessage(form.error);

  return (
    <>
      {banner === undefined ? null : <AuthNotice message={banner} />}

      <View style={s.form}>
        {/* No note under the name: it has no rule, and a form that explains one of two boxes
            leaves the other looking like the one with the rules — which is right. */}
        <TextField
          label={NAME_LABEL}
          value={form.name}
          onChangeText={form.setName}
          error={nameError}
          autoCapitalize="words"
          autoComplete="name"
          textContentType="name"
          editable={!form.pending}
        />

        <View style={s.box}>
          <TextField
            label={NICKNAME_LABEL}
            value={form.nickname}
            onChangeText={form.setNickname}
            error={nicknameError}
            // The rule reaches a listener with the box, and a reader under it — and it is
            // not drawn twice: when the box is refused, the refusal line has the sentence.
            accessibilityHint={NICKNAME_RULE}
            autoCapitalize="none"
            autoCorrect={false}
            textContentType="nickname"
            returnKeyType="go"
            onSubmitEditing={form.submit}
            editable={!form.pending}
          />
          {nicknameError === undefined ? <Text style={s.note}>{NICKNAME_RULE}</Text> : null}
        </View>
      </View>
    </>
  );
}

const s = StyleSheet.create({
  form: { gap: theme.space.md },
  box: { gap: theme.space.xxs },
  note: { ...theme.type.tiny, color: theme.color.muted },
});
