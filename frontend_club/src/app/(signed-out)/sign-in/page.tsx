import type { Metadata } from 'next';

import { SignInForm } from '@/features/sign-in/components/SignInForm';
import { signInNotice } from '@/features/sign-in/copy';
import { AuthCard } from '@/ui/AuthCard';

export const metadata: Metadata = { title: 'Sign in' };

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { session, 'signed-up': signedUp } = await searchParams;
  return (
    <AuthCard>
      <SignInForm notice={signInNotice(session, signedUp)} />
    </AuthCard>
  );
}
