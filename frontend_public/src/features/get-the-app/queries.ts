import 'server-only';

import { loadConfig } from '@/server/config';

import type { AppLinks } from './mappers';

/**
 * The links for a page about one of the app's routes: `join/<code>`, `invite/<token>`,
 * `reset/<token>`. **The route is the caller's to make safe**: it is put into the link as given.
 */
export function appLinks(route: string): AppLinks {
  const config = loadConfig();
  return {
    appStore: config.appStoreUrl,
    googlePlay: config.googlePlayUrl,
    openInRaketa: `${config.appScheme}://${route}`,
  };
}
