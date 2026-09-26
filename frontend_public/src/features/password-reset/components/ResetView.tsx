import { GetTheApp } from '@/features/get-the-app/components/GetTheApp';
import type { AppLinks } from '@/features/get-the-app/mappers';
import { LinkOutcome } from '@/features/set-password/components/LinkOutcome';
import { PasswordForm } from '@/features/set-password/components/PasswordForm';
import type { PasswordFormState } from '@/features/set-password/schemas';
import { PageTitle } from '@/ui/PageCard';

import { RESET_COPY, RESET_FORM, RESET_REFUSALS, RESET_STATES } from '../copy';
import type { ResetLink } from '../mappers';

/**
 * **The reset page, by the state of its link**, for a player or an administrator. While it works:
 * *Set a new password*, then the way in. Otherwise what the link is now (or, once the password was
 * set here, what to do next), and the way in.
 */
export function ResetView({
  link,
  justSet,
  links,
  setPassword,
}: {
  link: ResetLink;
  /** The page was reached by setting the password on it. */
  justSet: boolean;
  links: AppLinks;
  setPassword: (previous: PasswordFormState, form: FormData) => Promise<PasswordFormState>;
}) {
  if (link.state === 'valid') {
    return (
      <>
        <PageTitle title={RESET_COPY.title} lead={RESET_COPY.lead} />
        <PasswordForm action={setPassword} words={RESET_FORM} refusals={RESET_REFUSALS} />
        <GetTheApp links={links} />
      </>
    );
  }
  return (
    <>
      <PageTitle title={RESET_COPY.title} />
      <LinkOutcome
        state={link.state}
        justSet={justSet}
        done={RESET_COPY.done}
        states={RESET_STATES}
      />
      <GetTheApp links={links} />
    </>
  );
}
