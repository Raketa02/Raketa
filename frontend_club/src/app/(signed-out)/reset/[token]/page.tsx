import type { Metadata } from 'next';

import { setPasswordByLink } from '@/features/sign-in/actions';
import { NewPasswordForm } from '@/features/sign-in/components/NewPasswordForm';
import { AuthCard } from '@/ui/AuthCard';

/**
 * **The email's link**, `<CLUB_WEBSITE_URL>/reset/<token>` (the backend builds it). The token is
 * bound to the form's action on the server and posted back from there; the page sends
 * `Referrer-Policy: no-referrer` (next.config.ts), so the token never leaves in a `Referer`.
 */
export const metadata: Metadata = { title: 'Set a new password' };

export default async function ResetByLinkPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  return (
    <AuthCard>
      <NewPasswordForm via="link" action={setPasswordByLink.bind(null, token)} />
    </AuthCard>
  );
}
