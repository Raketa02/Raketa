import { GetTheApp } from '@/features/get-the-app/components/GetTheApp';
import type { AppLinks } from '@/features/get-the-app/mappers';
import { LinkOutcome } from '@/features/set-password/components/LinkOutcome';
import { PasswordForm } from '@/features/set-password/components/PasswordForm';
import type { PasswordFormState } from '@/features/set-password/schemas';
import { CodeBox } from '@/ui/CodeBox';
import { PageTitle } from '@/ui/PageCard';

import {
  greeting,
  INVITATION_COPY,
  INVITATION_FORM,
  INVITATION_REFUSALS,
  INVITATION_STATES,
} from '../copy';
import type { Invitation } from '../mappers';

/**
 * **The invitation page, by the state of its link.** While it works: the greeting, the code with
 * what to do with it, the way in, and *Set your password here*. Otherwise the greeting, what the
 * link is now (or, once the password was set here, what to do next), and the way in.
 */
export function InvitationView({
  invitation,
  justSet,
  links,
  setPassword,
}: {
  invitation: Invitation;
  /** The page was reached by setting the password on it. */
  justSet: boolean;
  links: AppLinks;
  setPassword: (previous: PasswordFormState, form: FormData) => Promise<PasswordFormState>;
}) {
  const title = <PageTitle title={greeting(invitation.name, invitation.club)} />;
  if (invitation.state === 'valid') {
    return (
      <>
        {title}
        <GetTheApp links={links} next={invitation.code === null ? undefined : INVITATION_COPY.next}>
          {invitation.code === null ? null : (
            <CodeBox label={INVITATION_COPY.code} code={invitation.code} />
          )}
        </GetTheApp>
        <PasswordForm action={setPassword} words={INVITATION_FORM} refusals={INVITATION_REFUSALS} />
      </>
    );
  }
  return (
    <>
      {title}
      <LinkOutcome
        state={invitation.state}
        justSet={justSet}
        done={INVITATION_COPY.done}
        states={INVITATION_STATES}
      />
      <GetTheApp links={links} />
    </>
  );
}
