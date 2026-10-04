import { expect, test } from './fixtures';
import { ANDROID_CERT_FINGERPRINTS, ANDROID_PACKAGE, APPLE_TEAM_ID, IOS_BUNDLE_ID } from './suite';

/**
 * **The app-link files** (#526, ADR-0187 §4, §7): what lets a tapped link open the app rather
 * than this site, once a domain exists. Each is generated from settings and served at its well-known
 * path as JSON, with no redirect, since neither Apple nor Android follows one.
 */

test("Apple's association file claims the group, invitation and reset links for the app", async ({
  request,
}) => {
  const response = await request.get('/.well-known/apple-app-site-association', {
    maxRedirects: 0,
  });

  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toBe('application/json');
  expect(await response.json()).toEqual({
    applinks: {
      details: [
        {
          appIDs: [`${APPLE_TEAM_ID}.${IOS_BUNDLE_ID}`],
          components: [
            { '/': '/join/*', comment: 'A group link' },
            { '/': '/invite/*', comment: "An administrator's invitation" },
            { '/': '/reset/*', comment: 'A password reset' },
          ],
        },
      ],
    },
  });
});

test("Android's asset links let the app handle this site's links, for each signing key", async ({
  request,
}) => {
  const response = await request.get('/.well-known/assetlinks.json', { maxRedirects: 0 });

  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toBe('application/json');
  expect(await response.json()).toEqual([
    {
      relation: ['delegate_permission/common.handle_all_urls'],
      target: {
        namespace: 'android_app',
        package_name: ANDROID_PACKAGE,
        // Upper case, as Android compares them.
        sha256_cert_fingerprints: ANDROID_CERT_FINGERPRINTS.map((key) => key.toUpperCase()),
      },
    },
  ]);
});
