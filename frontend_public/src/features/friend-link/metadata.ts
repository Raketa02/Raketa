import type { Metadata } from 'next';

import { SITE_COPY } from '@/ui/copy';
import { PREVIEW_TOKENS } from '@/ui/tokens';

import { invitedYou, wantsToBeYourFriend } from './copy';
import type { LinkOwner } from './mappers';

/** The two absolute addresses a preview names: the page's, and its face's. */
export interface PreviewLinks {
  readonly page: string;
  readonly image: string;
}

/**
 * **The friend link's preview tags** (ADR-0187 §4): what a messenger draws for the link, read from
 * the `<head>` the server sends. The title is the page's heading, whole, without the site's name
 * after it, since it already says *Raketa*; the line under it what the link comes to; the picture
 * the owner's face (`/face/<code>`), and none for somebody with no photograph.
 *
 * **It asks never to be listed**: the page names somebody and shows their face, by a link they
 * can turn off with New link, and a search engine's copy would outlive it.
 */
export function friendLinkPreview(owner: LinkOwner, links: PreviewLinks): Metadata {
  const title = invitedYou(owner.nickname);
  const description = wantsToBeYourFriend(owner.nickname);
  return {
    title: { absolute: title },
    description,
    robots: { index: false, follow: false },
    openGraph: {
      type: 'website',
      siteName: SITE_COPY.name,
      title,
      description,
      url: links.page,
      ...(owner.hasFace
        ? {
            images: [
              {
                url: links.image,
                width: PREVIEW_TOKENS.faceSide,
                height: PREVIEW_TOKENS.faceSide,
                alt: owner.nickname,
              },
            ],
          }
        : {}),
    },
    // A square picture beside the words, rather than a banner above them.
    twitter: { card: 'summary' },
  };
}
