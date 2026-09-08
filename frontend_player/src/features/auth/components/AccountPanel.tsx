/**
 * Who is signed in, and the way out.
 *
 * **A panel, not a screen, since the shell arrived.** It was `AccountScreen` — the
 * authenticated placeholder a player landed on past the entry gate — and it said so
 * provisionally, because the real app was unbuilt. The five-tab shell
 * ([#261](https://github.com/Raketa02/Raketa/issues/261)) is the app arriving: the landing is
 * now the Now tab, and this is what the **You** tab still carries. It keeps its chrome
 * nowhere and its title nowhere; the tab owns both.
 *
 * The identity is kept because it is how you tell *which* player the gate let through, and
 * sign-out is kept because it is the only way back to the beginning.
 *
 * The identity comes from `useCurrentUser`, not from the session: the profile is backend data
 * and Query owns it. That is also why this models a loading and an error state — a panel that
 * renders a name it assumes is already there is a panel that renders "undefined" on a cold
 * launch.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, theme } from '@/shared/ui';

import { useSignOut } from '../hooks/useAuthActions';
import { useCurrentUser } from '../hooks/useCurrentUser';

import { AuthNotice } from './AuthNotice';
import { authErrorMessage } from './authErrorMessage';

export function AccountPanel() {
  const user = useCurrentUser();
  const signOut = useSignOut();

  return (
    <View style={s.panel}>
      {user.data !== undefined ? (
        <Text style={s.body}>{`${user.data.nickname} · ${user.data.email}`}</Text>
      ) : null}

      {user.isPending ? <Text style={s.body}>Loading your profile…</Text> : null}

      {user.error !== null ? <AuthNotice message={authErrorMessage(user.error)} /> : null}

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
  );
}

const s = StyleSheet.create({
  panel: { gap: theme.space.md },
  body: { ...theme.type.tiny, color: theme.color.muted },
});
