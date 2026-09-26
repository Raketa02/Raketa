import { expect, signIn, test } from './fixtures';
import { administrator, DAY_MS, fromNow } from './stub/club';

/** **Every page works at phone width** (#500 story 95): nothing scrolls sideways at 360 px. */

test.use({ viewport: { width: 360, height: 780 } });

async function fitsSideways(page: import('@playwright/test').Page, path: string) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, `${path} scrolls sideways by ${overflow}px`).toBeLessThanOrEqual(0);
}

test('the signed-out pages fit a phone', async ({ page }) => {
  for (const path of [
    '/sign-in',
    '/sign-up',
    '/forgot-password',
    '/forgot-password/code',
    '/reset/a-link',
  ]) {
    await page.goto(path);
    await expect(page.getByText('Raketa for Clubs').first()).toBeVisible();
    await fitsSideways(page, path);
  }
});

test('the signed-in pages fit a phone, top bar and all', async ({ page, club }) => {
  void club;
  await signIn(page);
  for (const path of ['/overview', '/groups', '/administrators', '/details']) {
    await page.goto(path);
    await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Club website' })).toBeVisible();
    await fitsSideways(page, path);
  }
});

test('Administrators fits a phone: its rows, its form, its banner and its question', async ({
  page,
  club,
}) => {
  club.administrators = [
    administrator({
      name: 'Marta Wójcik',
      email: 'marta.wojcik.coaching@ogrody33-krakow.pl',
      status: 'ACTIVE',
      last_used_at: fromNow(-3 * DAY_MS),
      expires_at: null,
      groups: [
        { id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e01', name: 'Ogrody 33 Club' },
        { id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e02', name: 'Ogrody open play' },
      ],
      can_reset_password: true,
    }),
    administrator({ name: 'Tomek K.', email: 'tomek.k@gmail.com', status: 'EXPIRED' }),
  ];
  await signIn(page);
  await page.goto('/administrators');
  await page.getByText('2 groups').click();
  await fitsSideways(page, '/administrators');

  await page.getByRole('button', { name: '+ Add administrator' }).click();
  await page.getByLabel('Name', { exact: true }).fill('Robert');
  await page.getByLabel('Email', { exact: true }).fill('robert.constantin.dinescu@example.com');
  await fitsSideways(page, '/administrators, adding');

  await page.getByRole('button', { name: 'Send invitation', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Done' })).toBeVisible();
  await fitsSideways(page, '/administrators, sent');

  await page.getByRole('button', { name: 'Remove' }).first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await fitsSideways(page, '/administrators, removing');
});
