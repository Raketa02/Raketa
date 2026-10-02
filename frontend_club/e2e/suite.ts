/**
 * **The suite's own configuration**, read by `playwright.config.ts`, the fixtures and the fake
 * club, so each fact is written once: where the site and the stub listen, and the environment
 * the site is started with.
 */

export const SITE_PORT = 3100;
export const STUB_PORT = 4010;

const STUB = `http://127.0.0.1:${STUB_PORT}`;

/**
 * **Where the fake club's links to Stripe's hosted pages point** (#562): the stub draws them, as
 * it draws the map's tiles, so a redirect to Stripe lands somewhere real and nothing reaches
 * Stripe. Stripe sends the desk back to {@link STRIPE_RETURN_URL}, as the backend asks it to.
 */
export const STRIPE_PAGES = `${STUB}/stripe/setup`;
export const STRIPE_RETURN_URL = `http://127.0.0.1:${SITE_PORT}/overview`;

/** Where the map opens: `MAP_START` below, as the pages will read it. */
export const MAP_START = { latitude: 50.0614, longitude: 19.9366 };

export const SUITE_ENV = {
  APP_ENV: 'local',
  API_URL: STUB,
  SESSION_SECRET: 'e2e-only-session-secret-0123456789abcdef',
  MAP_TILE_URL: `${STUB}/tiles/{z}/{x}/{y}.png`,
  MAP_START: `${MAP_START.latitude},${MAP_START.longitude}`,
  NEXT_TELEMETRY_DISABLED: '1',
};
