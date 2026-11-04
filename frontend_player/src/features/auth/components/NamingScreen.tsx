/**
 * The naming step — *How should people see you?* — onboarding's first screen after sign-up.
 *
 * **It lives in `auth/`, not in `onboarding/`, on the second part's own precedent.** The
 * social steps sit in `player_profile/` because *the profile screen will later edit the same
 * values against the same rules*; the naming is the same shape. It is the users context's
 * one act on the player — `PUT /users/me/name`, repeatable, refused by the users context's
 * own conflict — and the You tab's *Nickname* edits it through the same form: `useNamingForm`
 * and `NamingFields` are the box and the act, and this file is the chrome the step puts
 * around them — the eyebrow, the question, *Continue*, and a back that is refused
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7). The route file under `(onboarding)/` is what makes it onboarding's screen; what it asks
 * is this feature's.
 *
 * **One box: a Nickname**, the handle every screen will say, unique across the platform
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). Nothing
 * is written under it until the player breaks its rule, and then the rule is the refusal. A
 * taken handle comes back by code with the field it belongs to, and it is rendered under the box
 * exactly as the sign-up conflicts always were; anything else stays in the banner.
 *
 * **It cannot be skipped, and the device's back is claimed and refused.** Every destination
 * after this one says the player's nickname, so the entry gate holds an account with none here —
 * and a press that walked out would land on whatever was under the group, which is nothing this
 * player may see yet. The screen draws no back control, and the hardware press does what the
 * missing control already says: nothing.
 *
 * **An account an Invitation opened is told what the nickname is for** (ADR-0199 §3–§4). It
 * holds no player name — the one its club typed stays the Administrator's — and reaches this step
 * through *Start playing*; under the title it reads *Pick a nickname — it's how players will see
 * you.* Every account sign-up creates sees the title alone.
 *
 * **On success it re-reads the player and hands the next step to the gate.** The mutation
 * writes what the server recorded into the cached player and *awaits* a fresh read of `/me`,
 * so by the time this screen navigates the cache is right and the server has confirmed it. It
 * then replaces itself with the app's root rather than with the next step directly: where a
 * named player belongs is the gate's rule and not this screen's.
 */

import { useRouter } from 'expo-router';
import { KeyboardAvoidingView, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { KEYBOARD_AVOIDANCE, useHardwareBack } from '@/shared/lib/platform';
import { Button, ScreenHeader, theme } from '@/shared/ui';

import { runsAClub } from '../domain/naming';
import { useCurrentUser } from '../hooks/useCurrentUser';
import { useNamingForm } from '../hooks/useNamingForm';

import { NamingFields } from './NamingFields';
import { CONTINUE, INVITED_LINE, NAMING_EYEBROW, NAMING_TITLE } from './namingPresentation';

export function NamingScreen() {
  const router = useRouter();
  const player = useCurrentUser().data;
  // An account that runs a club's groups is the sign of one an Invitation opened.
  const invited = player !== undefined && runsAClub(player);
  // The mutation has already written the recorded nickname into the cache and re-read the
  // player by the time this runs; the gate reads a named player and moves on.
  const form = useNamingForm({ onSaved: () => router.replace('/') });

  // Claimed and refused — see the module note. This screen draws no back control, and the
  // press does what the missing control already says.
  useHardwareBack(() => {});

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={s.flex} behavior={KEYBOARD_AVOIDANCE}>
        <ScreenHeader
          eyebrow={NAMING_EYEBROW}
          title={NAMING_TITLE}
          {...(invited ? { subline: INVITED_LINE } : {})}
        />

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
