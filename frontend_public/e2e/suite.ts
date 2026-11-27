/**
 * **The suite's own configuration**, read by `playwright.config.ts`, the fixtures and the specs,
 * so each fact is written once: where the site and the stub listen, and the environment the site
 * is started with. The ports are not the club website's, so the two suites can run side by side.
 */

export const SITE_PORT = 3200;
export const STUB_PORT = 4020;

const STUB = `http://127.0.0.1:${STUB_PORT}`;

/** The address this site is told it is reached at: deliberately not where the suite reaches it. */
export const SITE_URL = 'https://raketa.test';

export const APP_STORE_URL = 'https://apps.apple.com/app/raketa/id0000000001';
export const GOOGLE_PLAY_URL = 'https://play.google.com/store/apps/details?id=com.raketa.player';

/** The app the app-link files name: its Apple team and bundle, and its Android package and keys. */
export const APPLE_TEAM_ID = 'R4KET4TEAM';
export const IOS_BUNDLE_ID = 'com.raketa.player';
export const ANDROID_PACKAGE = 'com.raketa.player';
/** Two signing keys, as a release key and a store's re-signing key would be; written lower case. */
export const ANDROID_CERT_FINGERPRINTS = [
  'fa:c6:17:45:dc:09:03:78:6f:b9:ed:e6:2a:96:2b:39:9f:73:48:f0:bb:6f:89:9b:83:32:66:75:91:03:3b:9c',
  '14:6d:e9:83:c5:73:06:50:d8:ee:b9:95:2f:34:fc:64:16:a0:83:42:e6:1d:be:a8:8a:04:96:b2:3f:cf:44:e5',
];

export const SUITE_ENV = {
  APP_ENV: 'local',
  API_URL: STUB,
  PUBLIC_SITE_URL: SITE_URL,
  APP_STORE_URL,
  GOOGLE_PLAY_URL,
  APP_SCHEME: 'rakieta',
  APPLE_TEAM_ID,
  IOS_BUNDLE_ID,
  ANDROID_PACKAGE,
  ANDROID_CERT_FINGERPRINTS: ANDROID_CERT_FINGERPRINTS.join(', '),
  NEXT_TELEMETRY_DISABLED: '1',
};
