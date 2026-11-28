/**
 * Sign-in, sign-up, and *Forgot password?*.
 *
 * The mirror of the `(app)` guard: an authenticated player has no business on a sign-in
 * form, and without this redirect the sign-in screen stays mounted underneath after a
 * successful sign-in until something else navigates.
 *
 * **Recovering a password lives here too** (#515): the email form, the confirmation, the code
 * and *Set a new password* under `forgot-password/`, and the email's link at `reset/<token>`.
 * Setting one begins a session, and this redirect is what hands it to the entry gate — the
 * flow never navigates into the app itself.
 *
 * **Sign-in and sign-up cross-fade** ([#785](https://github.com/Rakieta02/Rakieta/issues/785), design
 * system 12.2): the two stage screens are two pages of one flow, so the move between them keeps the
 * frame where it is and changes what is in it, rather than sliding a second stage over the first. A
 * screen's `animation` is the one it is pushed **and** popped with, so sign-up's alone fades both
 * directions. **Sign-in keeps the platform's slide**: it is also the screen a recovery or invitation
 * screen opened from an email link puts in its own place, and those moves are not this one.
 */

import { Redirect, Stack } from 'expo-router';

import { useSessionStatus } from '@/shared/lib/auth';

export default function AuthLayout() {
  const status = useSessionStatus();

  if (status === 'bootstrapping') return null;

  if (status === 'authenticated') return <Redirect href="/" />;

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="sign-up" options={CROSS_FADE} />
    </Stack>
  );
}

/** Sign-up's move over sign-in and back — see the module note. */
const CROSS_FADE = { animation: 'fade' } as const;
