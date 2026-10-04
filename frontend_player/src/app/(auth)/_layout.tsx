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
 */

import { Redirect, Stack } from 'expo-router';

import { useSessionStatus } from '@/shared/lib/auth';

export default function AuthLayout() {
  const status = useSessionStatus();

  if (status === 'bootstrapping') return null;

  if (status === 'authenticated') return <Redirect href="/" />;

  return <Stack screenOptions={{ headerShown: false }} />;
}
