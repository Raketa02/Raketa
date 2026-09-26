import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { appLinks } from '@/features/get-the-app/queries';
import { ResetView } from '@/features/password-reset/components/ResetView';
import { RESET_COPY } from '@/features/password-reset/copy';
import { readResetLink, resetRoute } from '@/features/password-reset/queries';
import { setResetPassword } from '@/features/set-password/actions';
import { JUST_SET, wasJustSet } from '@/features/set-password/schemas';
import { SITE_COPY } from '@/ui/copy';
import { PageCard } from '@/ui/PageCard';

/**
 * **A reset's link**, `<PUBLIC_SITE_URL>/reset/<token>` (the backend builds it), for a player or
 * an administrator; a club's opens the club website's own page. The token is read on the server
 * and posted back from there, and every response sends `Referrer-Policy: no-referrer`.
 */

interface Props {
  params: Promise<{ token: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export const metadata: Metadata = {
  title: RESET_COPY.title,
  // A credential's page is never listed anywhere.
  robots: { index: false, follow: false },
};

export default async function ResetPage({ params, searchParams }: Props) {
  const { token } = await params;
  const link = await readResetLink(token);
  if (link === null) notFound();
  return (
    <PageCard brand={SITE_COPY.name}>
      <ResetView
        link={link}
        justSet={wasJustSet((await searchParams)[JUST_SET.param])}
        links={appLinks(resetRoute(token, link))}
        setPassword={setResetPassword.bind(null, token)}
      />
    </PageCard>
  );
}
