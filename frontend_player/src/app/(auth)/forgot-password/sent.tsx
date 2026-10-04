import { Redirect, useLocalSearchParams } from 'expo-router';

import { RESET_ROUTES, ResetSentScreen, parseEmailParam } from '@/features/auth/types';

/**
 * *Check your email* — the neutral confirmation (#515). It is about the address that was asked
 * with, so a visit with none has nothing to confirm and is sent to the form that asks.
 */
export default function ResetSentRoute() {
  const email = parseEmailParam(useLocalSearchParams());

  if (email === '') return <Redirect href={RESET_ROUTES.ask} />;

  return <ResetSentScreen email={email} />;
}
