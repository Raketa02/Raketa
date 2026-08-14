/**
 * Create an account.
 *
 * A server-side conflict — the email is taken, the nickname is taken — carries the field
 * it belongs to, so it is rendered under that box rather than in the banner. A player
 * told "that nickname is taken" above a four-field form still has to work out which box
 * to change.
 */

import { Link } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, theme } from '@/shared/ui';

import { useSignUp } from '../hooks/useAuthActions';
import { signUpSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthField, AuthNotice } from './AuthControls';
import { authErrorField, authErrorMessage } from './authErrorMessage';

export function SignUpScreen() {
  const [email, setEmail] = useState('');
  const [nickname, setNickname] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const signUp = useSignUp();

  const submit = () => {
    const result = validate(signUpSchema, {
      email,
      nickname,
      password,
      confirmPassword,
    });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    signUp.mutate({
      email: result.values.email,
      nickname: result.values.nickname,
      password: result.values.password,
    });
  };

  // A conflict the server raised against one field belongs under that field. Anything
  // else stays in the banner.
  const serverField = signUp.error === null ? undefined : authErrorField(signUp.error);
  const errorFor = (field: string) =>
    fieldErrors[field] ??
    (serverField === field && signUp.error !== null ? authErrorMessage(signUp.error) : undefined);

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={s.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={s.content}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
        >
          <View style={s.header}>
            <Text style={s.eyebrow}>Rakieta</Text>
            <Text style={s.title}>Create an account</Text>
          </View>

          {signUp.error !== null && serverField === undefined ? (
            <AuthNotice message={authErrorMessage(signUp.error)} />
          ) : null}

          <View style={s.form}>
            <AuthField
              label="Email"
              value={email}
              onChangeText={setEmail}
              error={errorFor('email')}
              autoCapitalize="none"
              autoComplete="email"
              autoCorrect={false}
              keyboardType="email-address"
              textContentType="emailAddress"
              editable={!signUp.isPending}
            />
            <AuthField
              label="Nickname"
              value={nickname}
              onChangeText={setNickname}
              error={errorFor('nickname')}
              autoCapitalize="none"
              autoCorrect={false}
              textContentType="nickname"
              editable={!signUp.isPending}
            />
            <AuthField
              label="Password"
              value={password}
              onChangeText={setPassword}
              error={errorFor('password')}
              secureTextEntry
              autoCapitalize="none"
              autoComplete="new-password"
              textContentType="newPassword"
              editable={!signUp.isPending}
            />
            <AuthField
              label="Repeat password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              error={errorFor('confirmPassword')}
              secureTextEntry
              autoCapitalize="none"
              autoComplete="new-password"
              textContentType="newPassword"
              returnKeyType="go"
              onSubmitEditing={submit}
              editable={!signUp.isPending}
            />
          </View>

          <Button
            label="Create account"
            size="lg"
            busyLabel="Creating account…"
            busy={signUp.isPending}
            onPress={submit}
          />

          <View style={s.footer}>
            <Text style={s.footerText}>Already have an account?</Text>
            <Link href="/sign-in" style={s.footerLink}>
              Sign in
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
  footerLink: { ...theme.type.rlValue, color: theme.color.ink },
});
