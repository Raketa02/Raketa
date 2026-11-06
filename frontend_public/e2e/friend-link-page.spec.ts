import { expect, test } from './fixtures';
import { portrait } from './photographs';
import { googlePlayLink } from './reading';
import { refusal } from './stub/backend';
import { FRIEND_LINK_PATH, tomek } from './stub/friends';
import { APP_STORE_URL, GOOGLE_PLAY_URL, SITE_URL } from './suite';

/**
 * **The friend link's page** (#755, the friends mechanics §4.3): Zofia taps Tomek's
 * `rakieta.app/f/<code>` on a phone without Raketa. The page says who invited her, with his face,
 * and shows the way in: the stores, and **Open in Raketa** for when she comes back.
 */

test('a friend link says who invited you, with their face', async ({ page, friendLinks }) => {
  friendLinks.seat('k7pq2mxa', tomek({ photo: await portrait(page) }));

  await page.goto('/f/k7pq2mxa');

  await expect(
    page.getByRole('heading', { level: 1, name: 'Tomek invited you to play on Raketa' }),
  ).toBeVisible();
  // His face, from this site, drawn: the backend's link to it is never put into the page.
  const face = page.getByRole('main').locator('img');
  await expect(face).toHaveAttribute('src', '/face/k7pq2mxa');
  await expect(face).toHaveJSProperty('naturalWidth', 300);
  expect(await page.content()).not.toContain('/storage/');
});

test('somebody with no photograph is drawn without a face', async ({ page, stub, friendLinks }) => {
  friendLinks.seat('k7pq2mxa', tomek({ photo: null }));

  await page.goto('/f/k7pq2mxa');

  await expect(
    page.getByRole('heading', { level: 1, name: 'Tomek invited you to play on Raketa' }),
  ).toBeVisible();
  await expect(page.getByRole('main').locator('img')).toHaveCount(0);
  expect(stub.storageOpened()).toEqual([]);
});

test('the page shows the way in: both stores, what to do once installed, and Open in Raketa', async ({
  page,
  friendLinks,
}) => {
  friendLinks.seat('k7pq2mxa');

  await page.goto('/f/k7pq2mxa');

  // An iPhone has no install referrer: the App Store button goes to the listing as it is.
  await expect(page.getByRole('link', { name: 'App Store' })).toHaveAttribute(
    'href',
    APP_STORE_URL,
  );
  // Android's carries the page's link through the install, which the app reads on first launch.
  expect(await googlePlayLink(page)).toEqual({
    listing: GOOGLE_PLAY_URL,
    referrer: `${SITE_URL}/f/k7pq2mxa`,
  });
  // The install forgets the link on an iPhone, so she comes back and taps it once more.
  await expect(
    page.getByText('Once you have the app, come back here and tap Open in Raketa'),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Open in Raketa' })).toHaveAttribute(
    'href',
    'raketa://f/k7pq2mxa',
  );
});

test('a code is read in any case, as the backend reads it', async ({ page, friendLinks }) => {
  friendLinks.seat('k7pq2mxa');

  await page.goto('/f/K7PQ2MXA');

  await expect(
    page.getByRole('heading', { level: 1, name: 'Tomek invited you to play on Raketa' }),
  ).toBeVisible();
});

test('a link replaced by a New link says Nothing at that link, answered 404', async ({
  page,
  friendLinks,
}) => {
  friendLinks.seat('k7pq2mxa');
  await page.goto('/f/k7pq2mxa');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Tomek invited you to play on Raketa',
  );

  friendLinks.replace('k7pq2mxa');
  const response = await page.goto('/f/k7pq2mxa');

  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1, name: 'Nothing at that link' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Open in Raketa' })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Google Play' })).toHaveCount(0);
});

test('a code no link ever carried says Nothing at that link', async ({ page }) => {
  const response = await page.goto('/f/zzzzzzzz');

  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1, name: 'Nothing at that link' })).toBeVisible();
});

test('a code that could be no link’s says Nothing at that link without asking the backend', async ({
  page,
  request,
  stub,
}) => {
  for (const code of ['k7pq-2mxa', 'k7pq%2F2mxa', 'k7pq2mx%C3%A5', 'k7pq2mxa%20']) {
    const response = await page.goto(`/f/${code}`);

    expect(response?.status(), code).toBe(404);
    await expect(page.getByRole('heading', { name: 'Nothing at that link' })).toBeVisible();
    expect((await request.get(`/face/${code}`)).status(), `the face of ${code}`).toBe(404);
  }
  expect(stub.requests('get', FRIEND_LINK_PATH)).toHaveLength(0);
});

test('a backend that fails says Something went wrong, never Nothing at that link', async ({
  page,
  stub,
}) => {
  for (const reply of [
    () => ({ status: 'drop' }) as const,
    () => ({ status: 503, body: refusal('service_unavailable') }) as const,
  ]) {
    stub.on('get', FRIEND_LINK_PATH, reply);

    const response = await page.goto('/f/k7pq2mxa');

    expect(response?.status()).toBe(500);
    await expect(page.getByRole('heading', { name: 'Something went wrong' })).toBeVisible();
    await expect(page.getByText('Nothing at that link')).toHaveCount(0);
  }
});

test.describe('without JavaScript', () => {
  test.use({ javaScriptEnabled: false });

  test('the whole page is there, face and all', async ({ browser, page, friendLinks }) => {
    // The photograph is drawn in a canvas, so in a page of its own that runs JavaScript.
    const darkroom = await browser.newPage();
    const photo = await portrait(darkroom);
    await darkroom.close();
    friendLinks.seat('k7pq2mxa', tomek({ photo }));

    await page.goto('/f/k7pq2mxa');

    await expect(
      page.getByRole('heading', { level: 1, name: 'Tomek invited you to play on Raketa' }),
    ).toBeVisible();
    await expect(page.getByRole('main').locator('img')).toHaveJSProperty('naturalWidth', 300);
    await expect(page.getByRole('link', { name: 'Open in Raketa' })).toBeVisible();
  });
});
