/**
 * **The test seam's fixtures**: a stub backend per worker, reset before every test and given the
 * fake group directory ({@link FakeGroups}) and the fake credentials ({@link FakeCredentials})
 * whether or not a test names them, so a group or a link nobody seated leads nowhere.
 *
 * The site under test is started once by `playwright.config.ts`, pointed at {@link STUB_PORT}.
 * The suite runs on one worker because that one server talks to one stub; each test resets it.
 */

import { expect, test as base } from '@playwright/test';

import { StubBackend } from './stub/backend';
import { FakeCredentials } from './stub/credentials';
import { FakeGroups } from './stub/groups';
import { STUB_PORT } from './suite';

interface Fixtures {
  stub: StubBackend;
  groups: FakeGroups;
  credentials: FakeCredentials;
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
  groups: [
    async ({ stub }, use) => {
      await use(new FakeGroups(stub).install());
    },
    { auto: true },
  ],
  credentials: [
    async ({ stub }, use) => {
      await use(new FakeCredentials(stub).install());
    },
    { auto: true },
  ],
});

export { expect };
