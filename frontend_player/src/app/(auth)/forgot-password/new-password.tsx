import { Redirect, useLocalSearchParams } from 'expo-router';

import {
  RESET_ROUTES,
  SetNewPasswordScreen,
  parseEmailParam,
  parseResetTicketParams,
} from '@/features/auth/types';

/**
 * *Set a new password* by a claimed code (#515) — pushed over the code screen with the ticket the
 * code bought, and the email the code was sent to so that *Ask again* does not ask for it twice.
 * A ticket that cannot be one has no password behind it, and the place a ticket comes from is the
 * code screen.
 */
export default function ResetNewPasswordRoute() {
  const params = useLocalSearchParams();
  const parsed = parseResetTicketParams(params);

  if (parsed === undefined) return <Redirect href={RESET_ROUTES.code} />;

  return (
    <SetNewPasswordScreen
      resetKey={{ via: 'code', ticket: parsed.ticket }}
      email={parseEmailParam(params)}
    />
  );
}
