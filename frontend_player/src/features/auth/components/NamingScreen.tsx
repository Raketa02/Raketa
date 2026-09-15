/**
 * The naming step — *How should people see you?* — onboarding's first screen after sign-up.
 *
 * **It lives in `auth/`, not in `onboarding/`, on the second part's own precedent.** The
 * social steps sit in `player_profile/` because *the profile screen will later edit the same
 * values against the same rules*; the naming is the same shape. It is the users context's
 * one act on the player — `PUT /users/me/name`, repeatable, refused by the users context's
 * own conflict — and the follow-up that edits the name from the You tab will drive the same
 * schema, the same mutation and the same sentences. The route file under `(onboarding)/`
 * is what makes it onboarding's screen; what it asks is this feature's.
 *
 * **Two boxes, one act.** A **Name** — whatever the player wants to be called, spaces
 * allowed, shared with anybody — and a **Nickname**, a handle under the rule the sign-up
 * form used to state, unique across the platform. The rule is written under its box before
 * anything is typed, so a refusal never surprises
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §1). A taken handle comes back by code with the field it belongs to, and it is rendered
 * under that box exactly as the sign-up conflicts always were; anything else stays in the
 * banner.
 *
 * **It cannot be skipped, and the device's back is claimed and refused.** Every destination
 * after this one says the player's name, so the entry gate holds an unnamed account here
 * (ADR-0171 §3) — and a press that walked out would land on whatever was under the group,
 * which is nothing this player may see yet. The screen draws no back control, and the
 * hardware press does what the missing control already says: nothing.
 *
 * **On success it re-reads the player and hands the next step to the gate.** The mutation
 * writes what the server recorded into the cached player and *awaits* a fresh read of `/me`
 * (ADR-0171 §3), so by the time this screen navigates the cache is right and the server has
 * confirmed it. It then replaces itself with the app's root rather than with `/welcome`
 * directly: where a named player belongs is the gate's rule and not this screen's — for the
 * ordinary player that is welcome, and for the shapes the flow cannot produce it is whatever
 * the gate says, exactly as the data screen exits the second part.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { KEYBOARD_AVOIDANCE, useHardwareBack } from '@/shared/lib/platform';
import { Button, ScreenHeader, TextField, theme } from '@/shared/ui';

import { useNamePlayer } from '../hooks/useAuthActions';
import { NICKNAME_RULE, namingSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthNotice } from './AuthNotice';
import { bannerMessage, errorUnderField } from './authErrorMessage';
import {
  CONTINUE,
  NAME_LABEL,
  NAMING_EYEBROW,
  NAMING_TITLE,
  NICKNAME_LABEL,
} from './namingPresentation';

export function NamingScreen() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [nickname, setNickname] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const naming = useNamePlayer();

  // Claimed and refused — see the module note. This screen draws no back control, and the
  // press does what the missing control already says.
  useHardwareBack(() => {});

  const submit = () => {
    const result = validate(namingSchema, { name, nickname });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    naming.mutate(result.values, {
      // The mutation has already written the recorded name into the cache and re-read the
      // player by the time this runs; the gate reads a named player and moves on.
      onSuccess: () => router.replace('/'),
    });
  };

  // A conflict the server raised against one field belongs under that field. Anything
  // else stays in the banner.
  const nameError = errorUnderField('name', fieldErrors, naming.error);
  const nicknameError = errorUnderField('nickname', fieldErrors, naming.error);
  const banner = bannerMessage(naming.error);

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={s.flex} behavior={KEYBOARD_AVOIDANCE}>
        <ScreenHeader eyebrow={NAMING_EYEBROW} title={NAMING_TITLE} />

        <ScrollView
          contentContainerStyle={s.content}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
        >
          {banner === undefined ? null : <AuthNotice message={banner} />}

          <View style={s.form}>
            {/* No note under the name: it has no rule, and a form that explains one of two
                boxes leaves the other looking like the one with the rules — which is right. */}
            <TextField
              label={NAME_LABEL}
              value={name}
              onChangeText={setName}
              error={nameError}
              autoCapitalize="words"
              autoComplete="name"
              textContentType="name"
              editable={!naming.isPending}
            />

            <View style={s.box}>
              <TextField
                label={NICKNAME_LABEL}
                value={nickname}
                onChangeText={setNickname}
                error={nicknameError}
                // The rule reaches a listener with the box, and a reader under it — and it is
                // not drawn twice: when the box is refused, the refusal line has the sentence.
                accessibilityHint={NICKNAME_RULE}
                autoCapitalize="none"
                autoCorrect={false}
                textContentType="nickname"
                returnKeyType="go"
                onSubmitEditing={submit}
                editable={!naming.isPending}
              />
              {nicknameError === undefined ? <Text style={s.note}>{NICKNAME_RULE}</Text> : null}
            </View>
          </View>
        </ScrollView>

        <View style={s.action}>
          <Button
            label={CONTINUE.label}
            size="lg"
            busyLabel={CONTINUE.busyLabel}
            busy={naming.isPending}
            onPress={submit}
            accessibilityHint={CONTINUE.hint}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  flex: { flex: 1 },
  content: {
    paddingHorizontal: theme.size.gutter,
    paddingBottom: theme.space.lg,
    gap: theme.space.lg,
  },
  form: { gap: theme.space.md },
  box: { gap: theme.space.xxs },
  note: { ...theme.type.tiny, color: theme.color.muted },
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
  },
});
