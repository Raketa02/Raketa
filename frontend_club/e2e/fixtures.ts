/**
 * **The test seam's fixtures**: a stub backend per worker, reset before every test and given the
 * one-club world ({@link FakeClub}), plus the small moves most tests begin with.
 *
 * The website under test is started once by `playwright.config.ts`, pointed at {@link STUB_PORT}.
 * The suite runs on one worker because that one server talks to one stub; each test resets it.
 */

import { expect, test as base, type Page } from '@playwright/test';

import { StubBackend } from './stub/backend';
import { DESK_EMAIL, DESK_PASSWORD, FakeClub } from './stub/club';
import { STUB_PORT } from './suite';

/** The cookie's name is part of what the browser sees, so the suite states it. */
export const SESSION_COOKIE = 'raketa_club_session';

interface Fixtures {
  stub: StubBackend;
  club: FakeClub;
}

interface WorkerFixtures {
  backend: StubBackend;
}

export const test = base.extend<Fixtures, WorkerFixtures>({
  backend: [
    // Playwright requires the destructuring even when a fixture uses none of the others.
    async ({}, use) => {
      const backend = await StubBackend.start(STUB_PORT);
      await use(backend);
      await backend.stop();
    },
    { scope: 'worker' },
  ],
  stub: async ({ backend }, use) => {
    backend.reset();
    await use(backend);
  },
  club: async ({ stub }, use) => {
    await use(new FakeClub(stub).install());
  },
});

export { expect };

/** Sign in through the sign-in page, as the desk does, and wait for Overview. */
export async function signIn(page: Page, email = DESK_EMAIL, password = DESK_PASSWORD) {
  await page.goto('/sign-in');
  await page.getByLabel('Club email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/overview$/);
}

/** Wait until the map has drawn and can take a pin. */
export async function mapReady(page: Page) {
  const map = page.getByRole('region', { name: 'Map of where the club is' });
  await expect(map).toHaveAttribute('data-ready', 'true');
  return map;
}
