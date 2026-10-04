import { defineConfig, devices } from '@playwright/test';

import { SITE_PORT, SUITE_ENV } from './e2e/suite';

/**
 * **The public site's test seam** (ADR-0187 §6): Playwright drives the built site while its
 * server layer talks to the stub backend in `e2e/stub/`, started by the worker
 * (`e2e/fixtures.ts`).
 *
 * The site is built and started once, on a port of its own, with a configuration made for the
 * suite: nothing here reads a developer's `.env.local` for its values, because every variable
 * is given. One worker, since the one server talks to the one stub.
 */

const PORT = SITE_PORT;

export default defineConfig({
  testDir: './e2e',
  workers: 1,
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `pnpm build && pnpm exec next start --hostname 127.0.0.1 --port ${PORT}`,
    // The one page that needs no backend: every other page asks the stub, which the worker
    // starts only after the server is up.
    url: `http://127.0.0.1:${PORT}/icon.svg`,
    env: SUITE_ENV,
    reuseExistingServer: false,
    timeout: 240_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
