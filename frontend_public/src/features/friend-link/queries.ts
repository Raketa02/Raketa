import 'server-only';

import { cache } from 'react';

import { appRoute } from '@/features/get-the-app/mappers';
import { isACode } from '@/features/group-page/schemas';
import { fromBackend } from '@/server/backend';
import { loadConfig } from '@/server/config';
import { fetchPhotograph } from '@/server/photos';

import { toFace, toReadOwner, type Face, type LinkOwner, type ReadOwner } from './mappers';
import type { PreviewLinks } from './metadata';

/**
 * **Who a friend link is from**, as the backend answers, or `null` when the link leads nowhere: a
 * code replaced by a New link, one no link ever carried, or one that could be no link's
 * (`friend_link_not_found`, #748). A friend link's code is shaped like a group's, so it is checked
 * as one. Read once per request, since the page and its preview tags both ask. Any other answer is
 * a failure the error page reports.
 */
const readOwner = cache(async (code: string): Promise<ReadOwner | null> => {
  if (!isACode(code)) return null;
  const outcome = await fromBackend((api) =>
    api.GET('/api/v1/public/friend-links/{code}', { params: { path: { code } } }),
  );
  if (outcome.ok) return toReadOwner(outcome.data);
  if (outcome.error.code === 'friend_link_not_found') return null;
  throw new Error(`Who a friend link is from could not be read: ${outcome.error.code}`);
});

/** The link's owner, as the page draws them, or `null` for a dead link. */
export async function readOwnerByLink(code: string): Promise<LinkOwner | null> {
  return (await readOwner(code))?.owner ?? null;
}

/**
 * **The owner's face**, or `null` for a dead link or somebody with no photograph. Asked for on its
 * own request, so it reads the link again and fetches the photograph by the link that read
 * signed: a signed link is never kept (#748). A photograph the storage would not give throws.
 */
export async function readFaceByLink(code: string): Promise<Face | null> {
  const photoLink = (await readOwner(code))?.photoLink ?? null;
  return photoLink === null ? null : toFace(await fetchPhotograph(photoLink));
}

/**
 * The route a friend link names, `f/<code>`, as the app and this site both spell it. Only for a
 * code {@link readOwnerByLink} found a link for, which is letters and digits.
 */
export function friendRoute(code: string): string {
  return appRoute('friend', code);
}

/**
 * Where this site serves the owner's face: outside `/f/`, which the app claims on a phone that
 * has it, as the group's tile is outside `/join/`.
 */
export function facePath(code: string): string {
  return `/face/${code}`;
}

/**
 * The preview's addresses, **at the address people reach this site by** (`PUBLIC_SITE_URL`): a
 * messenger fetches the face from there.
 */
export function previewLinks(code: string): PreviewLinks {
  const { siteUrl } = loadConfig();
  return { page: `${siteUrl}/${friendRoute(code)}`, image: `${siteUrl}${facePath(code)}` };
}
