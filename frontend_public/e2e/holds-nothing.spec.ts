import { expect, test } from './fixtures';
import { refusal } from './stub/backend';
import { GROUP_PATH } from './stub/groups';

/**
 * **The site holds nothing** (ADR-0187 §4, §6): no sign-in, no session, no cookie, and no
 * third-party script, and nothing a page's address carries leaves in a `Referer`. And when the
 * backend fails, the page says so rather than calling a live link dead.
 */

test('a page sets no cookie, loads no script from anywhere else, and sends no referrer', async ({
  page,
  groups,
}) => {
  groups.seat('k7pq2mxa');
  const scripts: string[] = [];
  page.on('request', (request) => {
    if (request.resourceType() === 'script') scripts.push(request.url());
  });

  const response = await page.goto('/join/k7pq2mxa');
  await expect(page.getByRole('heading', { level: 1, name: 'Ogrody 33 Club' })).toBeVisible();

  expect(await response?.headerValue('set-cookie')).toBeNull();
  expect(await page.context().cookies()).toEqual([]);
  expect(await response?.headerValue('referrer-policy')).toBe('no-referrer');
  const site = new URL(page.url()).origin;
  expect(scripts.filter((url) => new URL(url).origin !== site)).toEqual([]);
});

test('the backend asked with no session, and nothing else', async ({ page, stub, groups }) => {
  groups.seat('k7pq2mxa');

  await page.goto('/join/k7pq2mxa');

  const [asked] = stub.requests('get', GROUP_PATH);
  expect(asked?.params.code).toBe('k7pq2mxa');
  expect(asked?.headers.authorization).toBeUndefined();
  expect(asked?.headers.cookie).toBeUndefined();
});

test('a backend nobody can reach says Something went wrong, never Nothing at that link', async ({
  page,
  stub,
}) => {
  stub.on('get', GROUP_PATH, () => ({ status: 'drop' }));

  const response = await page.goto('/join/k7pq2mxa');

  expect(response?.status()).toBe(500);
  await expect(page.getByRole('heading', { name: 'Something went wrong' })).toBeVisible();
  await expect(page.getByText('Nothing at that link')).toHaveCount(0);
});

test('a backend that fails says Something went wrong, and the preview image is not drawn', async ({
  page,
  request,
  stub,
}) => {
  stub.on('get', GROUP_PATH, () => ({ status: 503, body: refusal('service_unavailable') }));

  const response = await page.goto('/join/k7pq2mxa');

  expect(response?.status()).toBe(500);
  await expect(page.getByRole('heading', { name: 'Something went wrong' })).toBeVisible();
  expect((await request.get('/preview/k7pq2mxa')).status()).toBe(500);
});
