import 'server-only';

import { loadConfig } from '@/server/config';

import type { AppLinks } from './mappers';

/**
 * The links for a page about one of the app's routes: `join/<code>`, `f/<code>`,
 * `invite/<token>`, `reset/<token>`. **The route is the caller's to make safe**: it is put into
 * the links as given.
 *
 * **`carryThroughInstall`** puts the page's own link, `<PUBLIC_SITE_URL>/<route>` as the backend
 * prints it, on the Google Play button as the **install referrer**: Play hands it to the app on
 * its first launch, which opens it as if it had been tapped (the friends mechanics §4.3, #756).
 * An iPhone has no such thing, so the App Store button is the listing as it is. Only a group link
 * and a friend link ask for it: Play keeps a referrer for 90 days, and a token is a credential.
 */
export function appLinks(
  route: string,
  { carryThroughInstall = false }: { carryThroughInstall?: boolean } = {},
): AppLinks {
  const config = loadConfig();
  return {
    appStore: config.appStoreUrl,
    googlePlay: carryThroughInstall
      ? withInstallReferrer(config.googlePlayUrl, `${config.siteUrl}/${route}`)
      : config.googlePlayUrl,
    openInRaketa: `${config.appScheme}://${route}`,
  };
}

/** The listing with `referrer` set, encoded as a query value, whatever else the listing carries. */
function withInstallReferrer(listing: string, link: string): string {
  const url = new URL(listing);
  url.searchParams.set('referrer', link);
  return url.toString();
}
