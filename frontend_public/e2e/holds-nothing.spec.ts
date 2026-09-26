import { expect, test } from './fixtures';
import { refusal } from './stub/backend';
import { token } from './stub/credentials';
import { GROUP_PATH } from './stub/groups';
import { SITE_PORT } from './suite';

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

test('an invitation’s token goes nowhere but this site, and setting the password sets no cookie', async ({
  page,
  credentials,
}) => {
  const link = token(201);
  credentials.invite(link);
  const elsewhere: string[] = [];
  const cookies: string[] = [];
  const site = `http://127.0.0.1:${SITE_PORT}`;
  page.on('request', (request) => {
    if (new URL(request.url()).origin !== site) elsewhere.push(request.url());
  });
  page.on('response', async (response) => {
    const cookie = await response.headerValue('set-cookie');
    if (cookie !== null) cookies.push(cookie);
  });

  const response = await page.goto(`/invite/${link}`);
  expect(await response?.headerValue('referrer-policy')).toBe('no-referrer');
  await page.getByLabel('Password', { exact: true }).fill('ogrody33club');
  await page.getByLabel('Repeat password').fill('ogrody33club');
  await page.getByRole('button', { name: 'Set password' }).click();
  await expect(page.getByText(/^Password set\./)).toBeVisible();

  expect(elsewhere).toEqual([]);
  expect(cookies).toEqual([]);
  expect(await page.context().cookies()).toEqual([]);
});

test('a credential’s page is never listed by a search engine', async ({ request, credentials }) => {
  credentials.invite(token(202));
  credentials.reset(token(203));

  for (const path of [`/invite/${token(202)}`, `/reset/${token(203)}`]) {
    const html = await (await request.get(path)).text();
    expect(html, path).toContain('<meta name="robots" content="noindex, nofollow"/>');
  }
});
