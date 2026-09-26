import { Redirect, useLocalSearchParams } from 'expo-router';

import {
  INVITATION_ROUTES,
  InvitationLinkScreen,
  parseInvitationLinkParams,
} from '@/features/auth/types';

/**
 * *Set your password* by the invitation email's button (#518) — `invite/<token>`, the path the
 * email names, which the links ticket (#520) opens from an incoming link. The token is input from
 * outside the app: one that cannot be one is a link this app cannot read, and the other door into an
 * invitation is the code form.
 */
export default function InvitationLinkRoute() {
  const parsed = parseInvitationLinkParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href={INVITATION_ROUTES.code} />;

  return <InvitationLinkScreen token={parsed.token} />;
}
