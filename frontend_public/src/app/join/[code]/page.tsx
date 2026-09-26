import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { GetTheApp } from '@/features/get-the-app/components/GetTheApp';
import { appLinks } from '@/features/get-the-app/queries';
import { GroupCard } from '@/features/group-page/components/GroupCard';
import { GROUP_PAGE_COPY } from '@/features/group-page/copy';
import { groupPreview } from '@/features/group-page/metadata';
import { groupRoute, previewLinks, readGroupByLink } from '@/features/group-page/queries';
import { SITE_COPY } from '@/ui/copy';
import { PageCard } from '@/ui/PageCard';

/**
 * **A group link**, `<PUBLIC_SITE_URL>/join/<code>` (the backend builds it, ADR-0183 §4), opened
 * by somebody without the app.
 */

interface Props {
  params: Promise<{ code: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { code } = await params;
  const group = await readGroupByLink(code);
  // A dead link's title is not-found.tsx's, where the page's notFound() sends it.
  return group === null ? {} : groupPreview(group, previewLinks(code));
}

export default async function GroupPage({ params }: Props) {
  const { code } = await params;
  const group = await readGroupByLink(code);
  if (group === null) notFound();
  return (
    <PageCard brand={SITE_COPY.name}>
      <GroupCard group={group} />
      <GetTheApp links={appLinks(groupRoute(code))} next={GROUP_PAGE_COPY.pasteInstruction} />
    </PageCard>
  );
}
