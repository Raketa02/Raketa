import { expect, test } from './fixtures';
import { refusal } from './stub/backend';
import { INVITATION_PASSWORD, INVITATION_READ, invitation, token } from './stub/credentials';
import { APP_STORE_URL, GOOGLE_PLAY_URL } from './suite';

/**
 * **The invitation page** (#526, #500 story 112): Marta opens her invitation email on her laptop
 * and clicks the button. The page greets her, offers the stores, shows her code with what to do
 * with it, and lets her set her password right there.
 */

test('an invitation link greets the person by name for the club, with the code and the way in', async ({
  page,
  stub,
  credentials,
}) => {
  const link = token(1);
  credentials.invite(link);

  await page.goto(`/invite/${link}`);

  // The whole name the club typed: nothing invents a first name (ADR-0171 §4).
  await expect(
    page.getByRole('heading', {
      level: 1,
      name: 'Hi Marta Wójcik — Ogrody 33 wants you as an administrator',
    }),
  ).toBeVisible();
  await expect(page.getByText('K7PQ2MXA', { exact: true })).toBeVisible();
  await expect(page.getByText('After you install, open Raketa and enter this code')).toBeVisible();
  await expect(page.getByRole('link', { name: 'App Store' })).toHaveAttribute(
    'href',
    APP_STORE_URL,
  );
  // No install referrer: Play would keep the link, and its token, for 90 days.
  await expect(page.getByRole('link', { name: 'Google Play' })).toHaveAttribute(
    'href',
    GOOGLE_PLAY_URL,
  );
  await expect(page.getByRole('link', { name: 'Open in Raketa' })).toHaveAttribute(
    'href',
    `raketa://invite/${link}`,
  );
  // The token went in a body, never a path, as the contract has it.
  expect(stub.requests('post', INVITATION_READ).map((request) => request.body)).toEqual([
    { token: link },
  ]);
});

test('Set your password here sets it by the link, then says to open Raketa and sign in', async ({
  page,
  stub,
  credentials,
}) => {
  const link = token(2);
  credentials.invite(link);
  await page.goto(`/invite/${link}`);

  await expect(
    page.getByRole('heading', { level: 2, name: 'Set your password here' }),
  ).toBeVisible();
  await page.getByLabel('Password', { exact: true }).fill('ogrody33club');
  await page.getByLabel('Repeat password').fill('ogrody33club');
  await page.getByRole('button', { name: 'Set password' }).click();

  await expect(
    page.getByText('Password set. Open Raketa and sign in with your email and password.'),
  ).toBeVisible();
  expect(stub.requests('post', INVITATION_PASSWORD).map((request) => request.body)).toEqual([
    { token: link, password: 'ogrody33club' },
  ]);
  // The link is spent: its code no longer opens anything, and there is nothing left to set.
  await expect(page.getByText('K7PQ2MXA')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Set password' })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Open in Raketa' })).toHaveAttribute(
    'href',
    'raketa://',
  );
});

test('a password the rule refuses, or typed differently twice, never leaves the page', async ({
  page,
  stub,
  credentials,
}) => {
  const link = token(3);
  credentials.invite(link);
  await page.goto(`/invite/${link}`);
  const password = page.getByLabel('Password', { exact: true });
  const again = page.getByLabel('Repeat password');
  const set = page.getByRole('button', { name: 'Set password' });

  await set.click();
  await expect(page.getByText('Type a password.')).toBeVisible();

  await password.fill('ogrody');
  await set.click();
  await expect(password).toHaveAccessibleDescription(
    'Use 8 to 128 characters, with at least one letter and one digit.',
  );
  await expect(password).toHaveAttribute('aria-invalid', 'true');

  await password.fill('ogrody33club');
  await set.click();
  await expect(page.getByText('Repeat your password.')).toBeVisible();

  await again.fill('ogrody33klub');
  await set.click();
  await expect(again).toHaveAccessibleDescription("Those passwords don't match.");
  // What was typed stays, and the refusal goes as soon as the box changes.
  await expect(password).toHaveValue('ogrody33club');
  await again.fill('ogrody33club');
  await expect(page.getByText("Those passwords don't match.")).toHaveCount(0);

  expect(stub.requests('post', INVITATION_PASSWORD)).toHaveLength(0);
});

test("the backend's refusals land where they belong: the rule under the box, the rest over the form", async ({
  page,
  stub,
  credentials,
}) => {
  const link = token(4);
  credentials.invite(link, invitation(), { accountExists: true });
  await page.goto(`/invite/${link}`);
  await page.getByLabel('Password', { exact: true }).fill('ogrody33club');
  await page.getByLabel('Repeat password').fill('ogrody33club');
  const set = page.getByRole('button', { name: 'Set password' });

  await set.click();
  await expect(page.getByRole('main').getByRole('alert')).toHaveText(
    'This email already has an account. Sign in to the app with it, and accept the invitation there.',
  );

  stub.on('post', INVITATION_PASSWORD, () => ({
    status: 400,
    body: refusal('password_too_weak', 'password'),
  }));
  await set.click();
  await expect(page.getByLabel('Password', { exact: true })).toHaveAccessibleDescription(
    'Use 8 to 128 characters, with at least one letter and one digit.',
  );

  stub.on('post', INVITATION_PASSWORD, () => ({ status: 'drop' }));
  await set.click();
  await expect(page.getByRole('main').getByRole('alert')).toHaveText(
    "We couldn't reach the server. Try again in a moment.",
  );
});

for (const [state, sentence] of [
  ['expired', 'That link has expired. Ask the club to send a new one.'],
  ['used', 'That link has already been used. Sign in to the app with the password you set.'],
  [
    'locked',
    'Too many wrong codes were typed for that invitation, so its link is locked too. Ask the club to send a new one.',
  ],
] as const) {
  test(`a link that is ${state} says so, with no code and nothing to set`, async ({
    page,
    credentials,
  }) => {
    const link = token(10 + state.length);
    credentials.invite(link, invitation({ state, code: null }));

    await page.goto(`/invite/${link}`);

    await expect(
      page.getByRole('heading', {
        level: 1,
        name: 'Hi Marta Wójcik — Ogrody 33 wants you as an administrator',
      }),
    ).toBeVisible();
    await expect(page.getByRole('main').getByRole('status')).toHaveText(sentence);
    await expect(page.getByText('Your code')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Set password' })).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Open in Raketa' })).toHaveAttribute(
      'href',
      'raketa://',
    );
  });
}

for (const [state, sentence] of [
  ['expired', 'That link has expired. Ask the club to send a new one.'],
  ['used', 'That link has already been used. Sign in to the app with the password you set.'],
  [
    'locked',
    'Too many wrong codes were typed for that invitation, so its link is locked too. Ask the club to send a new one.',
  ],
] as const) {
  test(`a link that becomes ${state} while the page is open says so when the password is set`, async ({
    page,
    credentials,
  }) => {
    const link = token(20 + state.length);
    credentials.invite(link);
    await page.goto(`/invite/${link}`);
    credentials.invite(link, invitation({ state }));

    await page.getByLabel('Password', { exact: true }).fill('ogrody33club');
    await page.getByLabel('Repeat password').fill('ogrody33club');
    await page.getByRole('button', { name: 'Set password' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText(sentence);
    await expect(page.getByRole('button', { name: 'Set password' })).toHaveCount(0);
  });
}

test('a link that stops being one while the page is open says Nothing at that link', async ({
  page,
  credentials,
}) => {
  const link = token(9);
  credentials.invite(link);
  await page.goto(`/invite/${link}`);
  credentials.forget(link);

  await page.getByLabel('Password', { exact: true }).fill('ogrody33club');
  await page.getByLabel('Repeat password').fill('ogrody33club');
  await page.getByRole('button', { name: 'Set password' }).click();

  await expect(page.getByRole('heading', { level: 1, name: 'Nothing at that link' })).toBeVisible();
});

test('a backend that fails to read the link says Something went wrong, never Nothing at that link', async ({
  page,
  stub,
}) => {
  stub.on('post', INVITATION_READ, () => ({
    status: 503,
    body: refusal('service_unavailable'),
  }));

  const response = await page.goto(`/invite/${token(10)}`);

  expect(response?.status()).toBe(500);
  await expect(page.getByRole('heading', { name: 'Something went wrong' })).toBeVisible();
});

test('a link never sent says Nothing at that link, and one that could be nobody’s is not asked about', async ({
  page,
  stub,
}) => {
  const response = await page.goto(`/invite/${token(6)}`);

  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { level: 1, name: 'Nothing at that link' })).toBeVisible();

  for (const odd of ['abc.def', 'abc%2Fdef', 'ab%20cd']) {
    expect((await page.goto(`/invite/${odd}`))?.status(), odd).toBe(404);
  }
  expect(stub.requests('post', INVITATION_READ)).toHaveLength(1);
});

test('a mark written by hand on a link that still works changes nothing', async ({
  page,
  credentials,
}) => {
  const link = token(7);
  credentials.invite(link);

  await page.goto(`/invite/${link}?password=set`);

  await expect(page.getByRole('button', { name: 'Set password' })).toBeVisible();
  await expect(
    page.getByText('Password set. Open Raketa and sign in with your email and password.'),
  ).toHaveCount(0);
});

test.describe('without JavaScript', () => {
  test.use({ javaScriptEnabled: false });

  // Setting the password needs JavaScript: under `Referrer-Policy: no-referrer` (ADR-0187 §6) a
  // browser posts a plain form with `Origin: null`, which Next refuses as a cross-site action.
  test('the page reads all the same: the greeting, the code and the way in', async ({
    page,
    credentials,
  }) => {
    const link = token(8);
    credentials.invite(link);

    await page.goto(`/invite/${link}`);

    await expect(
      page.getByRole('heading', {
        level: 1,
        name: 'Hi Marta Wójcik — Ogrody 33 wants you as an administrator',
      }),
    ).toBeVisible();
    await expect(page.getByText('K7PQ2MXA', { exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Open in Raketa' })).toBeVisible();
  });
});

test('a browser without JavaScript is told the form needs it, rather than failing when it is used', async ({
  request,
  credentials,
}) => {
  const link = token(11);
  credentials.invite(link);

  // Read from the HTML: Chromium with JavaScript turned off by Playwright still parses the page as
  // if it could run it, so it never draws a <noscript>.
  const html = await (await request.get(`/invite/${link}`)).text();

  expect(/<noscript>.*<\/noscript>/.exec(html)?.[0]).toContain(
    'Setting a password here needs JavaScript. Turn it on and reload this page, or set it in the app.',
  );
});
