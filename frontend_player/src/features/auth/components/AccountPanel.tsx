/**
 * The way out — *Sign out*, at the foot of the You tab.
 *
 * **A button, since the tab was built.** It was `AccountScreen`, the authenticated placeholder
 * a player landed on past the entry gate; the five-tab shell
 * ([#261](https://github.com/Raketa02/Raketa/issues/261)) made it a panel on the You tab —
 * the name, the handle, the email and the button — because the tab was a placeholder and the
 * panel was how you told *which* player the gate let through. The tab is built now
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1): the header card says the name and the handle, the *Name* row says them again and
 * changes them, and drawing them a third time at the foot would be the same fact three
 * times on one screen. What the panel keeps is what only it ever did — the button — at the
 * foot, as ADR-0179 §9 leaves it: the only way out of a session, and the one act on the tab
 * that is the account's rather than the profile's.
 *
 * **The email is drawn nowhere now**, and that is not an oversight: it has no row because it
 * has no route and no design (ADR-0179 §9), and a fact drawn with no door under a list of
 * facts with doors reads as a row that is broken.
 *
 * `dark`, not `primary`: coral is the accent an action *wants* you to take, and leaving is not
 * that action.
 */

import { StyleSheet, View } from 'react-native';

import { Button, theme } from '@/shared/ui';

import { useSignOut } from '../hooks/useAuthActions';

import { SIGN_OUT } from './accountPresentation';
import { AuthNotice } from './AuthNotice';
import { authErrorMessage } from './authErrorMessage';

export function AccountPanel() {
  const signOut = useSignOut();

  return (
    <View style={s.panel}>
      {signOut.error !== null ? <AuthNotice message={authErrorMessage(signOut.error)} /> : null}

      <Button
        label={SIGN_OUT.label}
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
  // A step above the last group, so the way out reads as the tab's foot and not as a row.
  panel: { gap: theme.space.md, paddingTop: theme.space.md },
});
