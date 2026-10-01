/**
 * **The suite's own configuration**, read by `playwright.config.ts`, the fixtures and the fake
 * club, so each fact is written once: where the site and the stub listen, and the environment
 * the site is started with.
 */

export const SITE_PORT = 3100;
export const STUB_PORT = 4010;

const STUB = `http://127.0.0.1:${STUB_PORT}`;

/** Where the map opens: `MAP_START` below, as the pages will read it. */
export const MAP_START = { latitude: 50.0614, longitude: 19.9366 };

export const SUITE_ENV = {
  APP_ENV: 'local',
  API_URL: STUB,
  SESSION_SECRET: 'e2e-only-session-secret-0123456789abcdef',
  MAP_TILE_URL: `${STUB}/tiles/{z}/{x}/{y}.png`,
  MAP_START: `${MAP_START.latitude},${MAP_START.longitude}`,
  GEOCODER_URL: `${STUB}/geocoder/search`,
  NEXT_TELEMETRY_DISABLED: '1',
};
