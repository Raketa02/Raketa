import { expect, signIn, test } from './fixtures';

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
