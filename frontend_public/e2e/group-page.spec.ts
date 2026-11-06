import { expect, test } from './fixtures';
import { googlePlayLink } from './reading';
import { APP_STORE_URL, GOOGLE_PLAY_URL, SITE_URL } from './suite';

/**
 * **The group page** (#525, #500 story 47): Kasia taps Marta's link without the app and lands on
 * the group — its tile, name, club and district, sports and size — and is shown the way in.
 */

test('a group link opens the group: its tile, its name, where it plays, its sports and its size', async ({
  page,
  groups,
}) => {
  groups.seat('k7pq2mxa');

  await page.goto('/join/k7pq2mxa');

  await expect(page.getByRole('heading', { level: 1, name: 'Ogrody 33 Club' })).toBeVisible();
  await expect(page.getByText('O3', { exact: true })).toBeVisible();
  await expect(page.getByText('Ogrody 33 · Grzegórzki')).toBeVisible();
  await expect(page.getByRole('list', { name: 'Sports' }).getByRole('listitem')).toHaveText([
    'Padel',
  ]);
  await expect(page.getByText('11 members')).toBeVisible();
});

test('the page shows the way in: both stores, where the link goes after sign-up, and Open in Raketa', async ({
  page,
  groups,
}) => {
  groups.seat('k7pq2mxa');

  await page.goto('/join/k7pq2mxa');

  await expect(page.getByRole('link', { name: 'App Store' })).toHaveAttribute(
    'href',
    APP_STORE_URL,
  );
  // Android's carries the page's link through the install, which the app reads on first launch
  // (the friends mechanics §4.3): the person lands in the group without pasting anything.
  expect(await googlePlayLink(page)).toEqual({
    listing: GOOGLE_PLAY_URL,
    referrer: `${SITE_URL}/join/k7pq2mxa`,
  });
  await expect(page.getByText('After you sign up, paste this link in Play › Join')).toBeVisible();
  // For a phone where the app is installed and the link didn't open it: the app's own scheme.
  await expect(page.getByRole('link', { name: 'Open in Raketa' })).toHaveAttribute(
    'href',
    'raketa://join/k7pq2mxa',
  );
});
