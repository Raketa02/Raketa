/**
 * The authenticated placeholder — what a player who is past onboarding opens on.
 *
 * The walking skeleton needs *somewhere* on the far side of the guard, and sign-out is
 * genuinely this feature's surface — so this is the account screen rather than an
 * invented `home` feature with eight empty layers.
 *
 * **It says "Inside the app" on purpose, and provisionally.** A player reaching here has a
 * Skill rating, so the entry gate will send them straight back here on every later launch
 * rather than through onboarding again — and the screen naming that state is what makes the
 * gate's decision visible while the real app is still unbuilt. The nickname and email are
 * kept because they are how you tell *which* player the gate let through, and sign-out is
 * kept because it is the only way back to the beginning.
 *
 * The identity comes from `useCurrentUser`, not from the session: the profile is backend
 * data and Query owns it. That is also why this screen models a loading and an error
 * state — a screen that renders a name it assumes is already there is a screen that
 * renders "undefined" on a cold launch.
 */

import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, theme } from '@/shared/ui';

import { useSignOut } from '../hooks/useAuthActions';
import { useCurrentUser } from '../hooks/useCurrentUser';

import { AuthNotice } from './AuthControls';
import { authErrorMessage } from './authErrorMessage';

export function AccountScreen() {
  const user = useCurrentUser();
  const signOut = useSignOut();

  return (
    // `top` only, since the tab bar landed: the bar is a sibling *below* this screen and
    // already spends the bottom inset clearing the home indicator, so claiming it here
    // too leaves a band of dead paper between the sign-out button and the bar. Now has
    // been `['top']` since it became the home screen, for the same reason.
    <SafeAreaView style={s.screen} edges={['top']}>
      <View style={s.content}>
        <View style={s.header}>
          <Text style={s.eyebrow}>Signed in</Text>
          <Text style={s.title} accessibilityRole="header">
            Inside the app
          </Text>
          {user.data !== undefined ? (
            <Text style={s.body}>{`${user.data.nickname} · ${user.data.email}`}</Text>
          ) : null}
        </View>

        {user.isPending ? <Text style={s.body}>Loading your profile…</Text> : null}

        {user.error !== null ? <AuthNotice message={authErrorMessage(user.error)} /> : null}

        <Text style={s.body}>
          Onboarding is behind you. This is where the app itself arrives in later slices.
        </Text>

        <Button
          label="Sign out"
          // `dark`, not `primary`: coral is the accent an action *wants* you to take,
          // and leaving is not that action.
          variant="dark"
          size="lg"
          busyLabel="Signing out…"
          busy={signOut.isPending}
          onPress={() => signOut.mutate()}
        />
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.md,
  },
  header: { gap: theme.space.xxs },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  title: { ...theme.type.h1, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.muted },
});
