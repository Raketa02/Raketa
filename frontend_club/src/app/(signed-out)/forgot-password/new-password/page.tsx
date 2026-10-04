import type { Metadata } from 'next';
import { redirect } from 'next/navigation';

import { setPasswordByCode } from '@/features/sign-in/actions';
import { NewPasswordForm } from '@/features/sign-in/components/NewPasswordForm';
import { hasTicket } from '@/features/sign-in/queries';
import { AuthCard } from '@/ui/AuthCard';

export const metadata: Metadata = { title: 'Set a new password' };

export default async function NewPasswordByCodePage() {
  if (!(await hasTicket())) redirect('/forgot-password/code');
  return (
    <AuthCard>
      <NewPasswordForm via="code" action={setPasswordByCode} />
    </AuthCard>
  );
}
