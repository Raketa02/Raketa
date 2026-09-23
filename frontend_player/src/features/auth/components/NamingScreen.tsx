/**
 * The naming step — *How should people see you?* — onboarding's first screen after sign-up.
 *
 * **It lives in `auth/`, not in `onboarding/`, on the second part's own precedent.** The
 * social steps sit in `player_profile/` because *the profile screen will later edit the same
 * values against the same rules*; the naming is the same shape. It is the users context's
 * one act on the player — `PUT /users/me/name`, repeatable, refused by the users context's
 * own conflict — and the You tab's *Name* now edits it through the same form: `useNamingForm`
 * and `NamingFields` are the two boxes and the act, and this file is the chrome the step puts
 * around them — the eyebrow, the question, *Continue*, and a back that is refused
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7). The route file under `(onboarding)/` is what makes it onboarding's screen; what it asks
 * is this feature's.
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
import { KeyboardAvoidingView, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { KEYBOARD_AVOIDANCE, useHardwareBack } from '@/shared/lib/platform';
import { Button, ScreenHeader, theme } from '@/shared/ui';

import { useNamingForm } from '../hooks/useNamingForm';

import { NamingFields } from './NamingFields';
import { CONTINUE, NAMING_EYEBROW, NAMING_TITLE } from './namingPresentation';

export function NamingScreen() {
  const router = useRouter();
  // The mutation has already written the recorded name into the cache and re-read the player
  // by the time this runs; the gate reads a named player and moves on.
  const form = useNamingForm({ onSaved: () => router.replace('/') });

  // Claimed and refused — see the module note. This screen draws no back control, and the
  // press does what the missing control already says.
  useHardwareBack(() => {});

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={s.flex} behavior={KEYBOARD_AVOIDANCE}>
        <ScreenHeader eyebrow={NAMING_EYEBROW} title={NAMING_TITLE} />

        <ScrollView
          contentContainerStyle={s.content}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
        >
          <NamingFields form={form} />
        </ScrollView>

        <View style={s.action}>
          <Button
            label={CONTINUE.label}
            size="lg"
            busyLabel={CONTINUE.busyLabel}
            busy={form.pending}
            onPress={form.submit}
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
  action: {
    paddingHorizontal: theme.size.gutter,
    paddingTop: theme.space.md,
    paddingBottom: theme.space.lg,
  },
});
