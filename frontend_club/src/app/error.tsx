'use client';

import { AuthCard } from '@/ui/AuthCard';
import { Button } from '@/ui/Button';
import { SITE_COPY } from '@/ui/copy';

/** A page that could not be drawn, most often because the backend could not be reached. */
export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <AuthCard title={SITE_COPY.error.title} lead={SITE_COPY.error.lead}>
      <Button type="button" onClick={reset}>
        {SITE_COPY.error.retry}
      </Button>
    </AuthCard>
  );
}
