import type { Metadata } from 'next';

import { mapSettings } from '@/features/club-details/queries';
import { SignUpForm } from '@/features/sign-in/components/SignUpForm';
import { SIGN_UP_COPY } from '@/features/sign-in/copy';
import { AuthCard } from '@/ui/AuthCard';

export const metadata: Metadata = { title: 'Sign up' };

export default async function SignUpPage() {
  return (
    <AuthCard wide title={SIGN_UP_COPY.title} lead={SIGN_UP_COPY.lead}>
      <SignUpForm map={await mapSettings()} />
    </AuthCard>
  );
}
