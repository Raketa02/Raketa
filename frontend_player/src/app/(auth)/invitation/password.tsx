import { Redirect, useLocalSearchParams } from 'expo-router';

import {
  INVITATION_ROUTES,
  SetYourPasswordScreen,
  parseEmailParam,
  parseInvitationTicketParams,
} from '@/features/auth/types';

/**
 * *Set your password* by a claimed code (#518) — pushed over *Have an invitation code?* with the
 * ticket the code bought and the email it was sent to, which the screen locks. A ticket that cannot
 * be one has no password behind it, and the place a ticket comes from is the code form.
 */
export default function InvitationPasswordRoute() {
  const params = useLocalSearchParams();
  const parsed = parseInvitationTicketParams(params);

  if (parsed === undefined) return <Redirect href={INVITATION_ROUTES.code} />;

  return (
    <SetYourPasswordScreen
      invitationKey={{ via: 'code', ticket: parsed.ticket }}
      email={parseEmailParam(params)}
    />
  );
}
