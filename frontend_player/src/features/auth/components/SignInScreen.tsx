/**
 * Sign in.
 *
 * The screen owns rendering and interaction. It owns no rule: what a valid email looks
 * like is `schemas/`, what signing in does is `use-cases/`, and what a failure means is
 * the error model. A `disabled={…}` expression encoding a rule would be a rule nobody
 * can test.
 */

import { Link } from "expo-router";
import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { theme } from "@/shared/ui/theme";

import { useSignIn } from "../hooks/useAuthActions";
import { signInSchema, validate, type FieldErrors } from "../schemas/authForms";

import { AuthButton, AuthField, AuthNotice } from "./AuthControls";
import { authErrorMessage } from "./authErrorMessage";

export function SignInScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const signIn = useSignIn();

  const submit = () => {
    const result = validate(signInSchema, { email, password });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    signIn.mutate(result.values);
  };

  return (
    <SafeAreaView style={s.screen} edges={["top", "bottom"]}>
      <KeyboardAvoidingView
        style={s.flex}
        // The keyboard covers the submit button on iOS otherwise; Android's
        // windowSoftInputMode already handles it and would double-inset.
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={s.content}
          keyboardShouldPersistTaps="handled"
          // The form must stay reachable when large text makes it taller than the screen.
          keyboardDismissMode="on-drag"
        >
          <View style={s.header}>
            <Text style={s.eyebrow}>Rakieta</Text>
            <Text style={s.title}>Sign in</Text>
          </View>

          {signIn.error !== null ? (
            <AuthNotice message={authErrorMessage(signIn.error)} />
          ) : null}

          <View style={s.form}>
            <AuthField
              label="Email"
              value={email}
              onChangeText={setEmail}
              error={fieldErrors.email}
              autoCapitalize="none"
              autoComplete="email"
              autoCorrect={false}
              keyboardType="email-address"
              textContentType="username"
              returnKeyType="next"
              editable={!signIn.isPending}
            />
            <AuthField
              label="Password"
              value={password}
              onChangeText={setPassword}
              error={fieldErrors.password}
              secureTextEntry
              autoCapitalize="none"
              autoComplete="current-password"
              textContentType="password"
              returnKeyType="go"
              onSubmitEditing={submit}
              editable={!signIn.isPending}
            />
          </View>

          <AuthButton
            label="Sign in"
            busyLabel="Signing in…"
            busy={signIn.isPending}
            onPress={submit}
          />

          <View style={s.footer}>
            <Text style={s.footerText}>New to Rakieta?</Text>
            <Link href="/sign-up" style={s.footerLink}>
              Create an account
            </Link>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  flex: { flex: 1 },
  content: {
    flexGrow: 1,
    justifyContent: "center",
    paddingHorizontal: theme.size.gutter,
    paddingVertical: theme.space.xxl,
    gap: theme.space.lg,
  },
  header: { gap: theme.space.xxs },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: "uppercase",
  },
  title: { ...theme.type.h1, color: theme.color.ink },
  form: { gap: theme.space.md },
  footer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    flexWrap: "wrap",
    gap: theme.space.xs,
  },
  footerText: { ...theme.type.tiny, color: theme.color.muted },
  footerLink: { ...theme.type.rlValue, color: theme.color.ink },
});
