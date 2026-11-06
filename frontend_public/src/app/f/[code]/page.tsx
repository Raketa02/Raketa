import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { OwnerCard } from '@/features/friend-link/components/OwnerCard';
import { FRIEND_LINK_COPY } from '@/features/friend-link/copy';
import { friendLinkPreview } from '@/features/friend-link/metadata';
import {
  facePath,
  friendRoute,
  previewLinks,
  readOwnerByLink,
} from '@/features/friend-link/queries';
import { GetTheApp } from '@/features/get-the-app/components/GetTheApp';
import { appLinks } from '@/features/get-the-app/queries';
import { SITE_COPY } from '@/ui/copy';
import { PageCard } from '@/ui/PageCard';

/**
 * **A friend link**, `<PUBLIC_SITE_URL>/f/<code>` (the backend builds it, #748), opened by
 * somebody without the app (the friends mechanics §4.3).
 */

interface Props {
  params: Promise<{ code: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { code } = await params;
  const owner = await readOwnerByLink(code);
  // A dead link's title is not-found.tsx's, where the page's notFound() sends it.
  return owner === null ? {} : friendLinkPreview(owner, previewLinks(code));
}

export default async function FriendLinkPage({ params }: Props) {
  const { code } = await params;
  const owner = await readOwnerByLink(code);
  if (owner === null) notFound();
  return (
    <PageCard brand={SITE_COPY.name}>
      <OwnerCard owner={owner} face={facePath(code)} />
      <GetTheApp
        links={appLinks(friendRoute(code), { carryThroughInstall: true })}
        next={FRIEND_LINK_COPY.comeBack}
      />
    </PageCard>
  );
}
