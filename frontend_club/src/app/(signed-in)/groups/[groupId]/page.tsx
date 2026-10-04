import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { GROUPS_COPY } from '@/features/groups/copy';
import { HandOver } from '@/features/groups/components/HandOver';
import { JoinRequests } from '@/features/groups/components/JoinRequests';
import { getGroupPage } from '@/features/groups/queries';
import { PageHeader } from '@/ui/PageHeader';

export const metadata: Metadata = { title: GROUPS_COPY.page.title };

/**
 * **An official group, as the club opens it from its table**: who waits to join, whom the club
 * answers (ADR-0191 §1), then who runs it and whom it can be handed to (ADR-0183 §8).
 */
export default async function GroupPage({ params }: { params: Promise<{ groupId: string }> }) {
  const page = await getGroupPage((await params).groupId);
  if (page === null) notFound();
  return (
    <>
      <PageHeader caption={GROUPS_COPY.page.caption} title={page.group.name} />
      <JoinRequests group={page.group} requests={page.requests} />
      <HandOver group={page.group} choices={page.choices} />
    </>
  );
}
