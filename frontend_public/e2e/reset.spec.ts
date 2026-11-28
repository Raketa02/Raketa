import { expect, test } from './fixtures';
import { refusal } from './stub/backend';
import { RESET_PASSWORD, RESET_READ, token } from './stub/credentials';

/**
 * **The reset page** (#526): Tomek asked for a new password in the app, opens the email on his
 * laptop, and sets it on the page. Setting it signs his account out everywhere and signs nobody
 * in, so the page then says to sign in to the app.
 */

test('a reset link sets a new password, then says to sign in to the app with it', async ({
  page,
  stub,
  credentials,
}) => {
  const link = token(101);
  credentials.reset(link);
  await page.goto(`/reset/${link}`);

  await expect(page).toHaveTitle('Set a new password · Rakieta');
  await expect(page.getByRole('heading', { level: 1, name: 'Set a new password' })).toBeVisible();
  await expect(page.getByText('Setting it signs your account out on every phone.')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Open in Rakieta' })).toHaveAttribute(
    'href',
    `rakieta://reset/${link}`,
  );
  expect(stub.requests('post', RESET_READ).map((request) => request.body)).toEqual([
    { token: link },
  ]);

  await page.getByLabel('New password', { exact: true }).fill('tomek2026k');
  await page.getByLabel('Repeat password').fill('tomek2026k');
  await page.getByRole('button', { name: 'Set password' }).click();

  await expect(page.getByRole('main').getByRole('status')).toHaveText(
    'New password set. Sign in to the app with your new password.',
  );
  expect(stub.requests('post', RESET_PASSWORD).map((request) => request.body)).toEqual([
    { token: link, password: 'tomek2026k' },
  ]);
  await expect(page.getByRole('button', { name: 'Set password' })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Open in Rakieta' })).toHaveAttribute(
    'href',
    'rakieta://',
  );
});

test('the password rule and the repeat are checked before anything leaves, and the backend’s rule lands under the box', async ({
  page,
  stub,
  credentials,
}) => {
  const link = token(102);
  credentials.reset(link);
  await page.goto(`/reset/${link}`);
  const password = page.getByLabel('New password', { exact: true });
  const set = page.getByRole('button', { name: 'Set password' });

  await password.fill('tomek');
  await set.click();
  await expect(password).toHaveAccessibleDescription(
    'Use 8 to 128 characters, with at least one letter and one digit.',
  );
  await password.fill('tomek2026k');
  await page.getByLabel('Repeat password').fill('tomek2026j');
  await set.click();
  await expect(page.getByText("Those passwords don't match.")).toBeVisible();
  expect(stub.requests('post', RESET_PASSWORD)).toHaveLength(0);

  stub.on('post', RESET_PASSWORD, () => ({
    status: 400,
    body: refusal('password_too_weak', 'password'),
  }));
  await page.getByLabel('Repeat password').fill('tomek2026k');
  await set.click();
  await expect(password).toHaveAccessibleDescription(
    'Use 8 to 128 characters, with at least one letter and one digit.',
  );

  stub.on('post', RESET_PASSWORD, () => ({ status: 'drop' }));
  await set.click();
  await expect(page.getByRole('main').getByRole('alert')).toHaveText(
    "We couldn't reach the server. Try again in a moment.",
  );
});

test('a backend that fails to read a reset link says Something went wrong', async ({
  page,
  stub,
}) => {
  stub.on('post', RESET_READ, () => ({ status: 503, body: refusal('service_unavailable') }));

  const response = await page.goto(`/reset/${token(105)}`);

  expect(response?.status()).toBe(500);
  await expect(page.getByRole('heading', { name: 'Something went wrong' })).toBeVisible();
});

for (const [state, sentence] of [
  [
    'expired',
    'That link has expired. To ask again for a new one, open the app and tap “Forgot password?”',
  ],
  [
    'used',
    'That link has already been used. Sign in to the app with your new password, or ask again for a new one.',
  ],
  [
    'locked',
    'Too many wrong codes were typed for that email, so its link is locked too. To ask again for a new one, open the app and tap “Forgot password?”',
  ],
] as const) {
  test(`a reset link that is ${state} says so, with nothing to set`, async ({
    page,
    credentials,
  }) => {
    const link = token(110 + state.length);
    credentials.reset(link, state);

    await page.goto(`/reset/${link}`);

    await expect(page.getByRole('heading', { level: 1, name: 'Set a new password' })).toBeVisible();
    await expect(page.getByRole('main').getByRole('status')).toHaveText(sentence);
    await expect(page.getByRole('button', { name: 'Set password' })).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Open in Rakieta' })).toHaveAttribute(
      'href',
      'rakieta://',
    );
  });
}

test('a reset link that expires while the page is open says so when the password is set', async ({
  page,
  credentials,
}) => {
  const link = token(103);
  credentials.reset(link);
  await page.goto(`/reset/${link}`);
  credentials.reset(link, 'expired');

  await page.getByLabel('New password', { exact: true }).fill('tomek2026k');
  await page.getByLabel('Repeat password').fill('tomek2026k');
  await page.getByRole('button', { name: 'Set password' }).click();

  await expect(page.getByRole('main').getByRole('status')).toHaveText(
    'That link has expired. To ask again for a new one, open the app and tap “Forgot password?”',
  );
});

test('a reset link never sent says Nothing at that link, and one that could be nobody’s is not asked about', async ({
  page,
  stub,
}) => {
  const response = await page.goto(`/reset/${token(104)}`);

  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1, name: 'Nothing at that link' })).toBeVisible();

  expect((await page.goto('/reset/abc.def'))?.status()).toBe(404);
  expect(stub.requests('post', RESET_READ)).toHaveLength(1);
});
