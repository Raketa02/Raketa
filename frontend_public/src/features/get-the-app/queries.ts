import 'server-only';

import { loadConfig } from '@/server/config';

/**
 * **Where the way in leads**: Raketa's two store listings, and the app itself at one of its own
 * routes. All three are settings (ADR-0187 §7), read here and handed to the page as addresses.
 */
export interface AppLinks {
  readonly appStore: string;
  readonly googlePlay: string;
  /** `<APP_SCHEME>://<route>`, which the app opens at that route (#520). */
  readonly openInRaketa: string;
}

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
