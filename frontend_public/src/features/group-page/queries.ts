import 'server-only';

import { cache } from 'react';

import { appRoute } from '@/features/get-the-app/mappers';
import { fromBackend } from '@/server/backend';
import { loadConfig } from '@/server/config';

import { toLinkedGroup, type LinkedGroup } from './mappers';
import type { PreviewLinks } from './metadata';

/**
 * **What a code could be**: letters and digits. The code arrives in the address, so it is
 * untrusted route input (ADR-0187 §7); anything else leads nowhere without asking the backend,
 * and nothing but letters and digits is ever put into a link this site draws.
 */
const A_CODE = /^[a-z0-9]{1,64}$/i;

/**
 * **The group a link opens**, or `null` when the link leads nowhere: no group has the code, it
 * could be nobody's, or its group was deleted (`group_not_found`, ADR-0183 §4). Read once per
 * request, since the page and its preview tags both ask: `cache` makes that one call, whatever
 * Next's own memoizing of `fetch` does. Any other answer is a failure the error page reports.
 */
export const readGroupByLink = cache(async (code: string): Promise<LinkedGroup | null> => {
  if (!A_CODE.test(code)) return null;
  const outcome = await fromBackend((api) =>
    api.GET('/api/v1/public/groups/{code}', { params: { path: { code } } }),
  );
  if (outcome.ok) return toLinkedGroup(outcome.data);
  if (outcome.error.code === 'group_not_found') return null;
  throw new Error(`The group a link opens could not be read: ${outcome.error.code}`);
});

/**
 * The route a group link names, `join/<code>`, as the app and this site both spell it: the app
 * opens it after `<APP_SCHEME>://`, and this site serves it. Only for a code
 * {@link readGroupByLink} found a group for, which is letters and digits.
 */
export function groupRoute(code: string): string {
  return appRoute('group', code);
}

/**
 * The preview's addresses, **at the address people reach this site by** (`PUBLIC_SITE_URL`), not
 * the one this process answers on: a messenger fetches the image from there.
 */
export function previewLinks(code: string): PreviewLinks {
  const { siteUrl } = loadConfig();
  return { page: `${siteUrl}/${groupRoute(code)}`, image: `${siteUrl}/preview/${code}` };
}
