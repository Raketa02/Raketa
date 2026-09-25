import { Redirect, useLocalSearchParams } from 'expo-router';

import { RESET_ROUTES, SetNewPasswordScreen, parseResetLinkParams } from '@/features/auth/types';

/**
 * *Set a new password* by the email's link (#515) — the address the email's button names,
 * `reset/<token>`, which the links ticket (#520) opens from an incoming link. The token is input
 * from outside the app: one that cannot be one is a link this app cannot read, and the honest
 * place to send whoever followed it is the form that asks for a working one.
 */
export default function ResetLinkRoute() {
  const parsed = parseResetLinkParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href={RESET_ROUTES.ask} />;

  return <SetNewPasswordScreen resetKey={{ via: 'link', token: parsed.token }} email="" />;
}
