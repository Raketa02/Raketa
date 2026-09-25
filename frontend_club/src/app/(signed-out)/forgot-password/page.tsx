import type { Metadata } from 'next';

import { ForgotPasswordForm } from '@/features/sign-in/components/ForgotPasswordForm';
import { recoveryEmail } from '@/features/sign-in/queries';
import { AuthCard } from '@/ui/AuthCard';

export const metadata: Metadata = { title: 'Forgot password' };

export default async function ForgotPasswordPage() {
  return (
    <AuthCard>
      <ForgotPasswordForm email={await recoveryEmail()} />
    </AuthCard>
  );
}
