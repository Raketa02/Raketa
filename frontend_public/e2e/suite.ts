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

export const SUITE_ENV = {
  APP_ENV: 'local',
  API_URL: STUB,
  PUBLIC_SITE_URL: SITE_URL,
  APP_STORE_URL,
  GOOGLE_PLAY_URL,
  APP_SCHEME: 'raketa',
  NEXT_TELEMETRY_DISABLED: '1',
};
