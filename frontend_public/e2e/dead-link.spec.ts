import { expect, test } from './fixtures';
import { GROUP_PATH } from './stub/groups';

/**
 * **A link that leads nowhere** (#500 story 37): no group has the code, its group was deleted, or
 * it could be nobody's. Each says *Nothing at that link*, answered 404, so that a messenger draws
 * no card for it.
 */

test('a code no group has says Nothing at that link, answered 404', async ({ page }) => {
  const response = await page.goto('/join/zzzzzzzz');

  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1, name: 'Nothing at that link' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Open in Raketa' })).toHaveCount(0);
});

test("a deleted group's link says Nothing at that link", async ({ page, groups }) => {
  groups.seat('k7pq2mxa');
  await page.goto('/join/k7pq2mxa');
  await expect(page.getByRole('heading', { level: 1, name: 'Ogrody 33 Club' })).toBeVisible();

  groups.delete('k7pq2mxa');
  const response = await page.goto('/join/k7pq2mxa');

  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1, name: 'Nothing at that link' })).toBeVisible();
});

test('a code that could be nobody’s says Nothing at that link without asking the backend', async ({
  page,
  stub,
}) => {
  for (const code of ['k7pq-2mxa', 'k7pq%2F2mxa', 'k7pq2mx%C3%A5', 'k7pq2mxa%20']) {
    const response = await page.goto(`/join/${code}`);

    expect(response?.status(), code).toBe(404);
    await expect(page.getByRole('heading', { name: 'Nothing at that link' })).toBeVisible();
  }
  expect(stub.requests('get', GROUP_PATH)).toHaveLength(0);
});

test('any other address on this site says Nothing at that link too', async ({ page }) => {
  const response = await page.goto('/groups/k7pq2mxa');

  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1, name: 'Nothing at that link' })).toBeVisible();
});
