/**
 * Create an account — **credentials, and nothing about who you are.**
 *
 * Email, a password twice and the adult attestation. The nickname left this form with
 * [ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §2: choosing credentials and saying who you are are two different moments, and the second
 * is onboarding's first screen — *How should people see you?* — which the entry gate sends
 * this new session straight into. A sign-up refused for a taken handle was a sign-up refused
 * for a reason that had nothing to do with the account.
 *
 * **It asks one question that is not about the account**: whether the player is an adult.
 * The platform is adults only and that is a precondition of holding an account rather than
 * a rule about who is shown to whom
 * ([ADR-0124](../../../../../docs/adr/0124-the-matcher-gates-account-state-never-age.md)),
 * so this form is where it is asked. What is collected is an **attestation** — one boolean,
 * never a date of birth, and **not age verification**. There is no date picker here and
 * this screen is not where the first one arrives.
 *
 * The box is never ticked on arrival, and the *Create account* button is never disabled by
 * it. A closed control is not a validation ([ADR-0089](../../../../../docs/adr/0089-player-profile-context-event-sourced.md)):
 * the press goes through, the form refuses, and it says what is missing under the box that
 * takes the answer. The same sentence renders when the server refuses the same thing by
 * code, because a body this form would not have sent can still arrive from an older build.
 *
 * A server-side conflict — the email is taken — carries the field it belongs to, so it is
 * rendered under that box rather than in the banner. A player told "that email already has
 * an account" above a three-field form still has to work out which box to change.
 *
 * **Both password boxes can be read back.** This is the one form in the app that asks for
 * the same secret twice and refuses on a mismatch, so a typo nobody can see costs the
 * player the whole form — and, on a phone whose keychain filled one box and not the other,
 * makes it impossible to tell what actually happened. Each box reveals on its own; showing
 * one says nothing about the other.
 */

import { Link } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { KEYBOARD_AVOIDANCE } from '@/shared/lib/platform';
import { Button, TextField, TickBox, theme } from '@/shared/ui';

import { useSignUp } from '../hooks/useAuthActions';
import { ADULT_LABEL, signUpSchema, validate, type FieldErrors } from '../schemas/authForms';

import { AuthNotice } from './AuthNotice';
import { bannerMessage, errorUnderField } from './authErrorMessage';

export function SignUpScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  /**
   * **False on arrival, and there is no path that starts it anywhere else.** A pre-ticked
   * box is a claim the player never made, which is the one thing an attestation exists to
   * rule out (ADR-0124).
   */
  const [adultAttested, setAdultAttested] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const signUp = useSignUp();

  const submit = () => {
    const result = validate(signUpSchema, {
      email,
      password,
      confirmPassword,
      adultAttested,
    });

    if (!result.ok) {
      setFieldErrors(result.fieldErrors);
      return;
    }

    setFieldErrors({});
    signUp.mutate({
      email: result.values.email,
      password: result.values.password,
      adultAttested: result.values.adultAttested,
    });
  };

  // A conflict the server raised against one field belongs under that field. Anything
  // else stays in the banner.
  const errorFor = (field: string) => errorUnderField(field, fieldErrors, signUp.error);
  const banner = bannerMessage(signUp.error);

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={s.flex} behavior={KEYBOARD_AVOIDANCE}>
        <ScrollView
          contentContainerStyle={s.content}
          keyboardShouldPersistTaps="handled"
          keyboardDismissMode="on-drag"
        >
          <View style={s.header}>
            <Text style={s.eyebrow}>Raketa</Text>
            <Text style={s.title}>Create an account</Text>
          </View>

          {banner === undefined ? null : <AuthNotice message={banner} />}

          <View style={s.form}>
            <TextField
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
            <TextField
              label="Password"
              value={password}
              onChangeText={setPassword}
              error={errorFor('password')}
              secureTextEntry
              reveal
              autoCapitalize="none"
              autoComplete="new-password"
              textContentType="newPassword"
              editable={!signUp.isPending}
            />
            <TextField
              label="Repeat password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              error={errorFor('confirmPassword')}
              secureTextEntry
              reveal
              autoCapitalize="none"
              autoComplete="new-password"
              textContentType="newPassword"
              returnKeyType="go"
              onSubmitEditing={submit}
              editable={!signUp.isPending}
            />

            {/* Below the three boxes and above the button, because it is the last thing a
                player agrees to rather than another detail about the account, and because
                a refusal has to be visible from the control that provoked it. */}
            <TickBox
              label={ADULT_LABEL}
              checked={adultAttested}
              onChange={setAdultAttested}
              error={errorFor('adultAttested')}
              disabled={signUp.isPending}
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
            {/* The same 44pt target the sign-in screen's link wears, and for the same
                reason — see `SignInScreen`. */}
            <Link href="/sign-in" asChild>
              <Pressable
                accessibilityRole="link"
                accessibilityLabel="Sign in"
                style={({ pressed }) => [s.footerTarget, pressed ? s.footerPressed : undefined]}
              >
                <Text style={s.footerLink}>Sign in</Text>
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
  footerTarget: {
    minHeight: theme.size.minTouch,
    justifyContent: 'center',
    paddingHorizontal: theme.space.xs,
  },
  footerPressed: { opacity: 0.6 },
  footerLink: { ...theme.type.rlValue, color: theme.color.ink },
});
