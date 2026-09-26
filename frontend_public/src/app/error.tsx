'use client';

import { SITE_COPY } from '@/ui/copy';
import { PageCard, PageTitle } from '@/ui/PageCard';
import { RetryButton } from '@/ui/RetryButton';

/**
 * **A page that could not be drawn**, most often because the backend could not be reached. Never
 * *Nothing at that link*: the link may well lead somewhere, and saying otherwise would send its
 * holder away.
 */
export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <PageCard brand={SITE_COPY.name}>
      <PageTitle title={SITE_COPY.error.title} lead={SITE_COPY.error.lead} />
      <RetryButton onRetry={reset}>{SITE_COPY.error.retry}</RetryButton>
    </PageCard>
  );
}
