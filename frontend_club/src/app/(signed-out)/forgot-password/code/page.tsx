import type { Metadata } from 'next';

import { ResetCodeForm } from '@/features/sign-in/components/ResetCodeForm';
import { recoveryEmail } from '@/features/sign-in/queries';
import { AuthCard } from '@/ui/AuthCard';

export const metadata: Metadata = { title: 'Enter the code' };

export default async function ResetCodePage() {
  return (
    <AuthCard>
      <ResetCodeForm email={await recoveryEmail()} />
    </AuthCard>
  );
}
