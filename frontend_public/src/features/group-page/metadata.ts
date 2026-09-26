import type { Metadata } from 'next';

import { SITE_COPY } from '@/ui/copy';
import { PREVIEW_TOKENS } from '@/ui/tokens';

import { previewLine } from './copy';
import type { LinkedGroup } from './mappers';

/** The two absolute addresses a preview names: the page's, and its image's. */
export interface PreviewLinks {
  readonly page: string;
  readonly image: string;
}

/**
 * **The group's preview tags** (ADR-0187 §4): what a messenger draws for the link, read from the
 * `<head>` the server sends. The title is the group's name, the line under it where it plays, its
 * sports and its size, and the image its tile (`/preview/<code>`).
 */
export function groupPreview(group: LinkedGroup, links: PreviewLinks): Metadata {
  const description = previewLine(group);
  return {
    title: group.name,
    description,
    openGraph: {
      type: 'website',
      siteName: SITE_COPY.name,
      title: group.name,
      description,
      url: links.page,
      images: [
        {
          url: links.image,
          width: PREVIEW_TOKENS.side,
          height: PREVIEW_TOKENS.side,
          alt: group.name,
        },
      ],
    },
    // A square picture beside the words, rather than a banner above them.
    twitter: { card: 'summary' },
  };
}
