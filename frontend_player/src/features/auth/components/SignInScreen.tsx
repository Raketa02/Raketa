/**
 * Sign in.
 *
 * The screen owns rendering and interaction. It owns no rule: what a valid email looks
 * like is `schemas/`, what signing in does is `use-cases/`, and what a failure means is
 * the error model. A `disabled={…}` expression encoding a rule would be a rule nobody
 * can test.
 *
 * **The password box can be read back**, exactly as both of the sign-up form's can. The
 * argument there was a typo nobody can see costing a player the whole form; here it is a
 * typo nobody can see costing them a refusal they cannot distinguish from a wrong password
 * — and a keychain that filled the box with the wrong entry looks identical either way. One
 * box, so the control's accessible name still says which field it is about and there is
 * nothing for it to be confused with.
 */

import { Link } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import { Button, TextField, theme } from '@/shared/ui';

import { useSignIn } from '../hooks/useAuthActions';
import { signInSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthNotice } from './AuthNotice';
import { authErrorMessage } from './authErrorMessage';

export function SignInScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        style={s.flex}
        // The keyboard covers the submit button on iOS otherwise; Android's
        // windowSoftInputMode already handles it and would double-inset.
        behavior={KEYBOARD_AVOIDANCE}
      >
        <ScrollView
          contentContainerStyle={s.content}
          keyboardShouldPersistTaps="handled"
          // The form must stay reachable when large text makes it taller than the screen.
          keyboardDismissMode="on-drag"
        >
          <View style={s.header}>
            <Text style={s.eyebrow}>Raketa</Text>
            <Text style={s.title}>Sign in</Text>
          </View>

          {signIn.error !== null ? <AuthNotice message={authErrorMessage(signIn.error)} /> : null}

          <View style={s.form}>
            <TextField
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
            <TextField
              label="Password"
              value={password}
              onChangeText={setPassword}
              error={fieldErrors.password}
              secureTextEntry
              reveal
              autoCapitalize="none"
              autoComplete="current-password"
              textContentType="password"
              returnKeyType="go"
              onSubmitEditing={submit}
              editable={!signIn.isPending}
            />
          </View>

          <Button
            label="Sign in"
            size="lg"
            busyLabel="Signing in…"
            busy={signIn.isPending}
            onPress={submit}
          />

          <View style={s.footer}>
            <Text style={s.footerText}>New to Raketa?</Text>
            {/* `asChild`, so the tappable thing is a real 44pt control rather than a line
                of text. A `Link` renders a `Text`, whose reachable area is exactly the
                glyphs — inside a `ScrollView`, a press that drifts a pixel becomes a scroll
                gesture instead, which is what made this take several attempts (6.5). */}
            <Link href="/sign-up" asChild>
              <Pressable
                accessibilityRole="link"
                accessibilityLabel="Create an account"
                style={({ pressed }) => [s.footerTarget, pressed ? s.footerPressed : undefined]}
              >
                <Text style={s.footerLink}>Create an account</Text>
              </Pressable>
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
    justifyContent: 'center',
    paddingHorizontal: theme.size.gutter,
    paddingVertical: theme.space.xxl,
    gap: theme.space.lg,
  },
  header: { gap: theme.space.xxs },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  title: { ...theme.type.h1, color: theme.color.ink },
  form: { gap: theme.space.md },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    flexWrap: 'wrap',
    gap: theme.space.xs,
  },
  footerText: { ...theme.type.tiny, color: theme.color.muted },
  // 44 by its own geometry rather than by slop: the target sits in a wrapping row, so
  // horizontal slop would be bounded by whatever ends up beside it (6.5).
  footerTarget: {
    minHeight: theme.size.minTouch,
    justifyContent: 'center',
    paddingHorizontal: theme.space.xs,
  },
  footerPressed: { opacity: 0.6 },
  footerLink: { ...theme.type.rlValue, color: theme.color.ink },
});
