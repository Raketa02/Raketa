import 'server-only';

import { APP_ROUTES } from '@/features/get-the-app/mappers';
import { loadConfig } from '@/server/config';

/**
 * **The app-link files** (ADR-0187 §4, §7): what tells iOS and Android that a link to this site
 * may open the player app instead, once a domain exists. Both are made from settings, never
 * literals, and read afresh per request, so a deploy's settings are the ones served.
 *
 * **Only Apple's file claims paths.** Android's says only that the app may handle this site's
 * links; which paths it takes is the app's own intent filters' business (#520).
 */

/**
 * The links the app opens itself (#520, #756). The preview images, the face included, and all
 * else stay with the site.
 */
const CLAIMED = [
  { '/': `/${APP_ROUTES.group}/*`, comment: 'A group link' },
  { '/': `/${APP_ROUTES.friend}/*`, comment: 'A friend link' },
  { '/': `/${APP_ROUTES.invitation}/*`, comment: "An administrator's invitation" },
  { '/': `/${APP_ROUTES.reset}/*`, comment: 'A password reset' },
];

/** Apple's association file, in the `applinks` form iOS 13 and later read. */
export function appleAssociation() {
  const { appleTeamId, iosBundleId } = loadConfig();
  return {
    applinks: {
      details: [{ appIDs: [`${appleTeamId}.${iosBundleId}`], components: CLAIMED }],
    },
  };
}

/** Android's asset links: the app, by its package and every key it is signed with. */
export function androidAssetLinks() {
  const { androidPackage, androidCertFingerprints } = loadConfig();
  return [
    {
      relation: ['delegate_permission/common.handle_all_urls'],
      target: {
        namespace: 'android_app',
        package_name: androidPackage,
        sha256_cert_fingerprints: androidCertFingerprints,
      },
    },
  ];
}
