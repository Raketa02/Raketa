import { Redirect, useLocalSearchParams } from 'expo-router';

import { RESET_ROUTES, SetNewPasswordScreen, parseResetLinkParams } from '@/features/auth/types';
import { useResetLinkOpened } from '@/features/links/types';

/**
 * *Set a new password* by the email's link (#515) — the address the email's button names,
 * `reset/<token>`, which an incoming link opens (#520) whenever nobody is signed in. The token is
 * input from outside the app: one that cannot be one is a link this app cannot read, and the honest
 * place to send whoever followed it is the form that asks for a working one.
 *
 * **The link is answered here**, so it is let go of: the password this screen sets begins a session,
 * and a link still held then would meet the signed-in phone as one to sign out of.
 */
export default function ResetLinkRoute() {
  const parsed = parseResetLinkParams(useLocalSearchParams());
  useResetLinkOpened(parsed?.token);

  if (parsed === undefined) return <Redirect href={RESET_ROUTES.ask} />;

  return <SetNewPasswordScreen resetKey={{ via: 'link', token: parsed.token }} email="" />;
}
