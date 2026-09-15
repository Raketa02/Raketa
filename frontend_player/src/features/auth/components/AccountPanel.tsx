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
 * **The identity is the name, the handle under it, and the email** — this is one of the two
 * screens that draw a player's `@nickname`
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §4), the other being the record. The name is what every other surface says about her; the
 * handle is what is hers alone, and this is where she reads it.
 *
 * The identity comes from `useCurrentUser`, not from the session: the profile is backend data
 * and Query owns it. That is also why this models a loading and an error state — a panel that
 * renders a name it assumes is already there is a panel that renders "undefined" on a cold
 * launch.
 */

import { StyleSheet, Text, View } from 'react-native';

import { atNickname } from '@/shared/formatting/playerName';
import { Button, theme } from '@/shared/ui';

import { useSignOut } from '../hooks/useAuthActions';
import { useCurrentUser } from '../hooks/useCurrentUser';

import { ACCOUNT_LOADING, SIGN_OUT, identityLabel } from './accountPresentation';
import { AuthNotice } from './AuthNotice';
import { authErrorMessage } from './authErrorMessage';

export function AccountPanel() {
  const user = useCurrentUser();
  const signOut = useSignOut();

  return (
    <View style={s.panel}>
      {user.data !== undefined ? (
        <View accessible accessibilityLabel={identityLabel(user.data)}>
          {/* The name in the card's own title role; the handle and the email under it are the
              small print they read as. Both the name and the handle are absent on an account
              held at the naming step, which never reaches this tab — dropped, not drawn empty. */}
          {user.data.name !== undefined ? <Text style={s.name}>{user.data.name}</Text> : null}
          {user.data.nickname !== undefined ? (
            <Text style={s.body}>{atNickname(user.data.nickname)}</Text>
          ) : null}
          <Text style={s.body}>{user.data.email}</Text>
        </View>
      ) : null}

      {user.isPending ? <Text style={s.body}>{ACCOUNT_LOADING}</Text> : null}

      {user.error !== null ? <AuthNotice message={authErrorMessage(user.error)} /> : null}

      <Button
        label={SIGN_OUT.label}
        // `dark`, not `primary`: coral is the accent an action *wants* you to take,
        // and leaving is not that action.
        variant="dark"
        size="lg"
        busyLabel={SIGN_OUT.busyLabel}
        busy={signOut.isPending}
        onPress={() => signOut.mutate()}
      />
    </View>
  );
}

const s = StyleSheet.create({
  panel: { gap: theme.space.md },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.muted },
});
