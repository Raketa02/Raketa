/**
 * *Check your email* — **the neutral confirmation**
 * ([#515](https://github.com/Raketa02/Raketa/issues/515),
 * [ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
 * §5).
 *
 * One sentence for everybody: *if* that email has an account, a link and a code went to it. The
 * address is said back because a typo is the likeliest reason nothing arrives, and saying it tells
 * nobody anything the person did not type. From here the code is one press away; the email's own
 * button opens *Set a new password* without this app's help.
 */

import { useRouter } from 'expo-router';

import { Button } from '@/shared/ui';

import { AuthFrame } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { RESET_COPY } from './resetPresentation';
import { RESET_ROUTES } from './resetRoutes';

export interface ResetSentScreenProps {
  /** The address that was asked with, as the form sent it. */
  readonly email: string;
}

export function ResetSentScreen({ email }: ResetSentScreenProps) {
  const router = useRouter();

  return (
    <AuthFrame title={RESET_COPY.sent.title} lead={RESET_COPY.sent.lead(email)}>
      <Button
        label={RESET_COPY.sent.enterCode}
        size="lg"
        onPress={() => router.push({ pathname: RESET_ROUTES.code, params: { email } })}
      />

      <AuthLink label={RESET_COPY.backToSignIn} onPress={() => router.dismissTo('/sign-in')} />
    </AuthFrame>
  );
}
