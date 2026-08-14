/**
 * The authenticated placeholder: who you are, and the way out.
 *
 * The walking skeleton needs *somewhere* on the far side of the guard, and sign-out is
 * genuinely this feature's surface — so this is the account screen rather than an
 * invented `home` feature with eight empty layers. The onboarding slice (#23) replaces
 * what the authenticated tree opens on.
 *
 * The nickname comes from `useCurrentUser`, not from the session: the profile is backend
 * data and Query owns it. That is also why this screen models a loading and an error
 * state — a screen that renders a name it assumes is already there is a screen that
 * renders "undefined" on a cold launch.
 */

import { StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { theme } from "@/shared/ui/theme";

import { useSignOut } from "../hooks/useAuthActions";
import { useCurrentUser } from "../hooks/useCurrentUser";

import { AuthButton, AuthNotice } from "./AuthControls";
import { authErrorMessage } from "./authErrorMessage";

export function AccountScreen() {
  const user = useCurrentUser();
  const signOut = useSignOut();

  return (
    <SafeAreaView style={s.screen} edges={["top", "bottom"]}>
      <View style={s.content}>
        <View style={s.header}>
          <Text style={s.eyebrow}>Signed in</Text>
          <Text style={s.title}>
            {user.data === undefined ? "Rakieta" : user.data.nickname}
          </Text>
          {user.data !== undefined ? (
            <Text style={s.body}>{user.data.email}</Text>
          ) : null}
        </View>

        {user.isPending ? <Text style={s.body}>Loading your profile…</Text> : null}

        {user.error !== null ? (
          <AuthNotice message={authErrorMessage(user.error)} />
        ) : null}

        <Text style={s.body}>
          Onboarding and the rest of the app arrive in later slices.
        </Text>

        <AuthButton
          label="Sign out"
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
    justifyContent: "center",
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.md,
  },
  header: { gap: theme.space.xxs },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: "uppercase",
  },
  title: { ...theme.type.h1, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.muted },
});
