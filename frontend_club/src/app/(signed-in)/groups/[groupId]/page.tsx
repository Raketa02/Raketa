import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { GROUPS_COPY } from '@/features/groups/copy';
import { HandOver } from '@/features/groups/components/HandOver';
import { getHandOver } from '@/features/groups/queries';
import { PageHeader } from '@/ui/PageHeader';

export const metadata: Metadata = { title: GROUPS_COPY.handOver.title };

export default async function HandOverPage({ params }: { params: Promise<{ groupId: string }> }) {
  const handOver = await getHandOver((await params).groupId);
  if (handOver === null) notFound();
  return (
    <>
      <PageHeader caption={GROUPS_COPY.handOver.caption} title={handOver.group.name} />
      <HandOver {...handOver} />
    </>
  );
}
