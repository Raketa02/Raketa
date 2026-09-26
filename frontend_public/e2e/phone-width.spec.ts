import type { Page } from '@playwright/test';

import { expect, test } from './fixtures';
import { invitation, token } from './stub/credentials';
import { GROUP_PATH, linkedGroup } from './stub/groups';

/**
 * **Laid out for phones first** (ADR-0187 §6): nothing scrolls sideways at 360 px, the narrowest
 * phone the club website is held to too. As a phone draws it: the page's viewport tag is obeyed,
 * where a desktop browser would ignore it.
 */

test.use({ viewport: { width: 360, height: 780 }, isMobile: true, hasTouch: true });

async function fitsSideways(page: Page, what: string) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, `${what} scrolls sideways by ${overflow}px`).toBeLessThanOrEqual(0);
}

test('the group page fits a phone, however long the name and however many the sports', async ({
  page,
  groups,
}) => {
  groups.seat('k7pq2mxa');
  groups.seat(
    'k7pq2mxb',
    linkedGroup({
      name: 'Ogrody33Club—wieczornegraniedlawszystkichchętnychzGrzegórzek',
      club: { name: 'Klub Sportowy Nowa Huta Arena', district: 'Wzgórza Krzesławickie' },
      sports: ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'],
      member_count: 1_152,
    }),
  );

  for (const code of ['k7pq2mxa', 'k7pq2mxb']) {
    await page.goto(`/join/${code}`);
    await expect(page.getByRole('link', { name: 'Open in Raketa' })).toBeVisible();
    await fitsSideways(page, `/join/${code}`);
  }
});

test('a dead link and a failing page fit a phone', async ({ page, stub }) => {
  await page.goto('/join/zzzzzzzz');
  await expect(page.getByRole('heading', { name: 'Nothing at that link' })).toBeVisible();
  await fitsSideways(page, 'a dead link');

  stub.on('get', GROUP_PATH, () => ({ status: 'drop' }));
  await page.goto('/join/k7pq2mxa');
  await expect(page.getByRole('heading', { name: 'Something went wrong' })).toBeVisible();
  await fitsSideways(page, 'a failing page');
});

test('the invitation and reset pages fit a phone, in every state, refusals and all', async ({
  page,
  credentials,
}) => {
  credentials.invite(
    token(301),
    invitation({
      name: 'Małgorzata Szczepańska-Wróblewska',
      club_name: 'Klub Sportowy Nowa Huta Arena',
    }),
  );
  credentials.invite(token(302), invitation({ state: 'locked', code: null }));
  credentials.reset(token(303));
  credentials.reset(token(304), 'expired');

  await page.goto(`/invite/${token(301)}`);
  await page.getByLabel('Password', { exact: true }).fill('short');
  await page.getByRole('button', { name: 'Set password' }).click();
  await expect(page.getByLabel('Password', { exact: true })).toHaveAttribute(
    'aria-invalid',
    'true',
  );
  await fitsSideways(page, 'an invitation, refused');

  for (const path of [`/invite/${token(302)}`, `/reset/${token(303)}`, `/reset/${token(304)}`]) {
    await page.goto(path);
    await expect(page.getByRole('link', { name: 'Open in Raketa' })).toBeVisible();
    await fitsSideways(page, path);
  }
});
