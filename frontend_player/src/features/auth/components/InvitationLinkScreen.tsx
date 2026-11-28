/**
 * ***Set your password*** **by the invitation email's button** — `invite/<token>`
 * ([#518](https://github.com/Rakieta02/Rakieta/issues/518), PRD #500 story 113). The links ticket
 * ([#520](https://github.com/Rakieta02/Rakieta/issues/520)) opens it from an incoming link; this is
 * the screen the link lands on.
 *
 * **The token is validated before anything is drawn**: the link is read first
 * (`POST /invitations/by-token`), and only a link that still works draws the form — with the email
 * the server read locked in its box. While the read is out the frame is drawn with its title and
 * nothing under it, so no form appears and then vanishes. A link that no longer works says why in
 * the sentence the set would have been refused with — expired, used, locked, or never sent — and
 * offers the way back to sign in; a read that could not be made says so and offers it again.
 */

import { useRouter } from 'expo-router';

import { useInvitationLink } from '../hooks/useInvitationLink';

import { AuthFrame } from './AuthFrame';
import { AuthLink } from './AuthLink';
import { AuthNotice } from './AuthNotice';
import {
  INVITATION_COPY,
  LINK_STATE_MESSAGE,
  invitationErrorMessage,
} from './invitationPresentation';
import { SetYourPasswordScreen } from './SetYourPasswordScreen';

const linkRefusal = invitationErrorMessage('link');

export function InvitationLinkScreen({ token }: { readonly token: string }) {
  const router = useRouter();
  const link = useInvitationLink(token);

  if (link.data?.state === 'valid') {
    return <SetYourPasswordScreen invitationKey={{ via: 'link', token }} email={link.data.email} />;
  }

  // Why the form is not drawn: the link is spent, or it could not be read. Neither while it is.
  const why =
    link.data !== undefined
      ? LINK_STATE_MESSAGE[link.data.state]
      : link.error === null
        ? undefined
        : linkRefusal(link.error);
  // **The retry follows the failure's recovery, never its code** (`groups`' `ReadFailure` rule): a
  // read the connection or the server lost may answer next time; a link never sent will not.
  const again =
    link.error?.recovery === 'retryable-automatically' ||
    link.error?.recovery === 'retryable-by-user';

  return (
    <AuthFrame title={INVITATION_COPY.password.title}>
      {why === undefined ? null : <AuthNotice message={why} />}

      {again ? (
        <AuthLink label={INVITATION_COPY.tryAgain} onPress={() => void link.refetch()} />
      ) : null}

      {link.isPending ? null : (
        <AuthLink
          label={INVITATION_COPY.backToSignIn}
          onPress={() => router.dismissTo('/sign-in')}
        />
      )}
    </AuthFrame>
  );
}
