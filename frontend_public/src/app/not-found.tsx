import type { Metadata } from 'next';

import { SITE_COPY } from '@/ui/copy';
import { PageCard, PageTitle } from '@/ui/PageCard';

export const metadata: Metadata = { title: SITE_COPY.notFound.title };

/**
 * **A link that leads nowhere**, and any other address here: every page on this site is reached
 * by a link, so both are a dead link (#500 story 37).
 */
export default function NotFound() {
  return (
    <PageCard brand={SITE_COPY.name}>
      <PageTitle title={SITE_COPY.notFound.title} lead={SITE_COPY.notFound.lead} />
    </PageCard>
  );
}
