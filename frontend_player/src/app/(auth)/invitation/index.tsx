import { useLocalSearchParams } from 'expo-router';

import { InvitationCodeScreen, parseEmailParam } from '@/features/auth/types';

/**
 * *Have an invitation code?* (#518) — reached from under the Sign in button with whatever its email
 * box held. The email only pre-fills a box, so one that does not parse opens it empty.
 */
export default function InvitationCodeRoute() {
  return <InvitationCodeScreen email={parseEmailParam(useLocalSearchParams())} />;
}
