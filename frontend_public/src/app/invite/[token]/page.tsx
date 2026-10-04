import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { appLinks } from '@/features/get-the-app/queries';
import { InvitationView } from '@/features/invitation/components/InvitationView';
import { INVITATION_COPY } from '@/features/invitation/copy';
import { invitationRoute, readInvitation } from '@/features/invitation/queries';
import { setInvitationPassword } from '@/features/set-password/actions';
import { JUST_SET, wasJustSet } from '@/features/set-password/schemas';
import { SITE_COPY } from '@/ui/copy';
import { PageCard } from '@/ui/PageCard';

/**
 * **An invitation's link**, `<PUBLIC_SITE_URL>/invite/<token>` (the backend builds it), opened by
 * a new administrator, most often on a laptop. The token is read on the server and posted back
 * from there, and every response sends `Referrer-Policy: no-referrer` (next.config.ts).
 */

interface Props {
  params: Promise<{ token: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export const metadata: Metadata = {
  title: INVITATION_COPY.title,
  // A credential's page is never listed anywhere.
  robots: { index: false, follow: false },
};

export default async function InvitePage({ params, searchParams }: Props) {
  const { token } = await params;
  const invitation = await readInvitation(token);
  if (invitation === null) notFound();
  return (
    <PageCard brand={SITE_COPY.name}>
      <InvitationView
        invitation={invitation}
        justSet={wasJustSet((await searchParams)[JUST_SET.param])}
        links={appLinks(invitationRoute(token, invitation))}
        setPassword={setInvitationPassword.bind(null, token)}
      />
    </PageCard>
  );
}
