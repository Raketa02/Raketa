/**
 * Sign-in and sign-up.
 *
 * The mirror of the `(app)` guard: an authenticated player has no business on a sign-in
 * form, and without this redirect the sign-in screen stays mounted underneath after a
 * successful sign-in until something else navigates.
 *
 * Password recovery belongs in this group and is **not** in scope — the player API
 * surface has no reset endpoint, so there is nothing to build against yet.
 */

import { Redirect, Stack } from 'expo-router';

import { useSessionStatus } from '@/shared/lib/auth';

export default function AuthLayout() {
  const status = useSessionStatus();

  if (status === 'bootstrapping') return null;

  if (status === 'authenticated') return <Redirect href="/" />;

  return <Stack screenOptions={{ headerShown: false }} />;
}
