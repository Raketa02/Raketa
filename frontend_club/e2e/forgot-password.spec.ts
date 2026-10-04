import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { DESK_EMAIL } from './stub/club';

const NEW_PASSWORD = 'nowe-haslo-33';

const SENT = (email: string) =>
  `If a club signs in with ${email}, we've sent it a link and an 8-character code. ` +
  'Both work for one hour, once.';

test.describe('Forgot password', () => {
  test('by the code: ask, enter the code, set a new password, and land signed in', async ({
    page,
    stub,
    club,
  }) => {
    await page.goto('/sign-in');
    await page.getByRole('link', { name: 'Forgot password?' }).click();
    await expect(page.getByRole('heading', { name: 'Forgot password?' })).toBeVisible();
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByRole('button', { name: 'Send' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText(SENT(DESK_EMAIL));
    const [mail] = club.outbox;
    if (mail === undefined) throw new Error('no email was sent');

    await page.getByRole('link', { name: 'Enter the code' }).click();
    await expect(page.getByRole('heading', { name: 'Enter the code' })).toBeVisible();
    // The email asked with is offered back.
    await expect(page.getByLabel('Club email')).toHaveValue(DESK_EMAIL);
    // Typed as a person types it: lower case, with a dash.
    await page
      .getByLabel('Code')
      .fill(`${mail.code.slice(0, 4)}-${mail.code.slice(4)}`.toLowerCase());
    await page.getByRole('button', { name: 'Continue' }).click();

    await expect(page).toHaveURL(/\/forgot-password\/new-password$/);
    await page.getByLabel('New password').fill(NEW_PASSWORD);
    await page.getByRole('button', { name: 'Set password' }).click();

    await expect(page).toHaveURL(/\/overview\?notice=password-set$/);
    await expect(page.getByRole('main').getByRole('status')).toHaveText(
      'New password set. Any other browser signed in as the club is signed out.',
    );
    await expect(page.getByRole('banner').getByRole('button', { name: 'Sign out' })).toBeVisible();

    expect(stub.requests('post', '/api/v1/club/auth/forgot-password/claim')[0]?.body).toEqual({
      email: DESK_EMAIL,
      code: mail.code,
    });
    const [set] = stub.requests('post', '/api/v1/club/auth/forgot-password/new-password');
    expect(set?.body).toEqual({ ticket: `ticket-for-${mail.code}`, password: NEW_PASSWORD });
    expect(club.password).toBe(NEW_PASSWORD);
  });

  test('by the link: /reset/<token> sets a new password and signs the club in', async ({
    page,
    stub,
    club,
  }) => {
    await page.goto('/forgot-password');
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByRole('button', { name: 'Send' }).click();
    await expect(page.getByRole('main').getByRole('status')).toBeVisible();
    const [mail] = club.outbox;
    if (mail === undefined) throw new Error('no email was sent');

    const response = await page.goto(`/reset/${mail.token}`);
    expect(response?.headers()['referrer-policy']).toBe('no-referrer');
    await page.getByLabel('New password').fill(NEW_PASSWORD);
    await page.getByRole('button', { name: 'Set password' }).click();

    await expect(page).toHaveURL(/\/overview\?notice=password-set$/);
    const [set] = stub.requests('post', '/api/v1/club/auth/forgot-password/new-password');
    expect(set?.body).toEqual({ token: mail.token, password: NEW_PASSWORD });
  });

  test('says the same sentence for an address no club signs in with', async ({ page, club }) => {
    await page.goto('/forgot-password');
    await page.getByLabel('Club email').fill('nobody@example.pl');
    await page.getByRole('button', { name: 'Send' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText(SENT('nobody@example.pl'));
    expect(club.outbox).toEqual([]);
  });

  test('another browser signed in as the club is signed out by the reset', async ({
    page,
    browser,
    club,
  }) => {
    const elsewhere = await browser.newContext();
    const desk = await elsewhere.newPage();
    await signIn(desk);

    await page.goto(`/forgot-password`);
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByRole('button', { name: 'Send' }).click();
    await expect(page.getByRole('main').getByRole('status')).toBeVisible();
    await page.goto(`/reset/${club.outbox[0]?.token}`);
    await page.getByLabel('New password').fill(NEW_PASSWORD);
    await page.getByRole('button', { name: 'Set password' }).click();
    await expect(page).toHaveURL(/\/overview\?notice=password-set$/);

    await desk.reload();
    await expect(desk).toHaveURL(/\/sign-in\?session=ended$/);
    await elsewhere.close();
  });

  test("an address the backend's own email check refuses is said under the email box", async ({
    page,
    stub,
  }) => {
    // The backend answers a 422 with its envelope, whatever the contract declares.
    stub.on('post', '/api/v1/club/auth/forgot-password', () => ({
      status: 422,
      body: refusal('validation_error'),
    }));
    await page.goto('/forgot-password');
    await page.getByLabel('Club email').fill('desk@ogrody33.local');
    await page.getByRole('button', { name: 'Send' }).click();

    await expect(page.getByText("That doesn't look like an email address.")).toBeVisible();
    await expect(page.getByLabel('Club email')).toHaveAttribute('aria-invalid', 'true');
  });

  test('a wrong code is refused under the code box', async ({ page, club }) => {
    void club;
    await page.goto('/forgot-password/code');
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByLabel('Code').fill('ZZZZZZZZ');
    await page.getByRole('button', { name: 'Continue' }).click();

    await expect(
      page.getByText("That isn't the code we sent to that email. Check it and type it again."),
    ).toBeVisible();
    await expect(page.getByLabel('Code')).toHaveAttribute('aria-invalid', 'true');
  });

  test('a code of the wrong length is refused before it spends an attempt', async ({
    page,
    stub,
  }) => {
    await page.goto('/forgot-password/code');
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByLabel('Code').fill('K7Q2');
    await page.getByRole('button', { name: 'Continue' }).click();

    await expect(page.getByText('The code is 8 characters.')).toBeVisible();
    expect(stub.all()).toEqual([]);
  });

  test('a locked code says to ask again, and links there', async ({ page, stub }) => {
    stub.on('post', '/api/v1/club/auth/forgot-password/claim', () => ({
      status: 409,
      body: refusal('credential_locked'),
    }));
    await page.goto('/forgot-password/code');
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByLabel('Code').fill('K7Q2M9X1');
    await page.getByRole('button', { name: 'Continue' }).click();

    const alert = page.getByRole('main').getByRole('alert');
    await expect(alert).toContainText(
      'Too many wrong codes were typed, so that one is locked. Ask again for a new one.',
    );
    await alert.getByRole('link', { name: 'Ask again' }).click();
    await expect(page.getByRole('heading', { name: 'Forgot password?' })).toBeVisible();
    await expect(page.getByLabel('Club email')).toHaveValue('');
  });

  test('an expired link says so, and the way out is to ask again', async ({ page, stub }) => {
    stub.on('post', '/api/v1/club/auth/forgot-password/new-password', () => ({
      status: 409,
      body: refusal('credential_expired'),
    }));
    await page.goto('/reset/an-old-link');
    await page.getByLabel('New password').fill(NEW_PASSWORD);
    await page.getByRole('button', { name: 'Set password' }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      'That link has expired. Ask again for a new one.',
    );
    await expect(page.getByRole('link', { name: 'Ask again' })).toHaveAttribute(
      'href',
      '/forgot-password',
    );
  });

  test('a ticket that ran out sends the desk back to the code, which still works', async ({
    page,
    stub,
    club,
  }) => {
    await page.goto('/forgot-password');
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByRole('button', { name: 'Send' }).click();
    await page.getByRole('link', { name: 'Enter the code' }).click();
    await expect(page.getByRole('heading', { name: 'Enter the code' })).toBeVisible();
    await page.getByLabel('Code').fill(club.outbox[0]?.code ?? '');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page).toHaveURL(/\/forgot-password\/new-password$/);

    stub.on('post', '/api/v1/club/auth/forgot-password/new-password', () => ({
      status: 409,
      body: refusal('ticket_expired'),
    }));
    await page.getByLabel('New password').fill(NEW_PASSWORD);
    await page.getByRole('button', { name: 'Set password' }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      'That took too long. Enter the code again.',
    );
    await page.getByRole('link', { name: 'Enter the code again' }).click();
    await expect(page.getByRole('heading', { name: 'Enter the code' })).toBeVisible();
    await expect(page.getByLabel('Club email')).toHaveValue(DESK_EMAIL);
  });

  test('a weak password is refused under its box with the rule, and nothing is sent', async ({
    page,
    stub,
  }) => {
    await page.goto('/reset/some-link');
    await page.getByLabel('New password').fill('short1');
    await page.getByRole('button', { name: 'Set password' }).click();

    await expect(page.getByLabel('New password')).toHaveAttribute('aria-invalid', 'true');
    await expect(
      page.getByText('Use 8 to 128 characters, with at least one letter and one digit.'),
    ).toBeVisible();
    expect(stub.all()).toEqual([]);
  });

  test('Set a new password by code without a claimed code goes back to the code', async ({
    page,
  }) => {
    await page.goto('/forgot-password/new-password');
    await expect(page).toHaveURL(/\/forgot-password\/code$/);
  });
});
