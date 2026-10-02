import { expect, signIn, test } from './fixtures';
import { DESK_EMAIL, DESK_PASSWORD } from './stub/club';

test.describe('Sign in', () => {
  test('the page is club mock 1: the wordmark, CLUB EMAIL, PASSWORD and Sign in', async ({
    page,
  }) => {
    await page.goto('/sign-in');

    await expect(page.getByText('Raketa for Clubs')).toBeVisible();
    await expect(page.getByLabel('Club email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Forgot password?' })).toHaveAttribute(
      'href',
      '/forgot-password',
    );
    await expect(page.getByRole('link', { name: 'Sign up' })).toHaveAttribute('href', '/sign-up');
  });

  test('the desk signs in and sees the frame: the pages, its club and Sign out', async ({
    page,
    club,
    stub,
  }) => {
    await signIn(page);

    const bar = page.getByRole('banner');
    await expect(bar.getByText('Raketa for Clubs')).toBeVisible();
    const pages = page.getByRole('navigation', { name: 'Club website' });
    await expect(pages.getByRole('link')).toHaveText([
      'Overview',
      'Bookings',
      'Courts & prices',
      'Money',
      'Groups',
      'Administrators',
    ]);
    await expect(pages.getByRole('link', { name: 'Overview' })).toHaveAttribute(
      'aria-current',
      'page',
    );
    await expect(bar.getByRole('button', { name: /Ogrody 33/ })).toHaveText(
      'Ogrody 33 · Grzegórzki, Kraków',
    );
    await expect(bar.getByRole('button', { name: 'Sign out' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();

    expect(stub.requests('post', '/api/v1/club/auth/login').map((r) => r.body)).toEqual([
      { email: DESK_EMAIL, password: DESK_PASSWORD },
    ]);
    // The frame read the club with the pair just issued.
    const reads = stub.requests('get', '/api/v1/club/details');
    expect(reads.length).toBeGreaterThan(0);
    expect(reads.every((r) => r.headers.authorization === `Bearer ${club.accessToken(1)}`)).toBe(
      true,
    );
    expect(club.details.name).toBe('Ogrody 33');
  });

  test('a wrong password is refused over the form, and nobody is signed in', async ({
    page,
    club,
    context,
  }) => {
    void club;
    await page.goto('/sign-in');
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByLabel('Password').fill('not-the-password1');
    await page.getByRole('button', { name: 'Sign in' }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "That email and password don't match. Try again.",
    );
    await expect(page).toHaveURL(/\/sign-in$/);
    expect(await context.cookies()).toEqual([]);
  });

  test('empty boxes are refused under each one, and nothing reaches the backend', async ({
    page,
    stub,
  }) => {
    await page.goto('/sign-in');
    await page.getByRole('button', { name: 'Sign in' }).click();

    await expect(page.getByText("Type the club's email.")).toBeVisible();
    await expect(page.getByText('Type the password.')).toBeVisible();
    await expect(page.getByLabel('Club email')).toHaveAttribute('aria-invalid', 'true');
    expect(stub.all()).toEqual([]);
  });

  test('a malformed email is refused under its box before anything is sent', async ({
    page,
    stub,
  }) => {
    await page.goto('/sign-in');
    await page.getByLabel('Club email').fill('desk@');
    await page.getByLabel('Password').fill(DESK_PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();

    await expect(page.getByText("That doesn't look like an email address.")).toBeVisible();
    // Typing in the box takes its refusal away.
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await expect(page.getByText("That doesn't look like an email address.")).toBeHidden();
    expect(stub.all()).toEqual([]);
  });

  test('a backend that does not answer is said plainly', async ({ page, stub }) => {
    stub.on('post', '/api/v1/club/auth/login', () => ({ status: 'drop' }));
    await page.goto('/sign-in');
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByLabel('Password').fill(DESK_PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "We couldn't reach the server. Try again in a moment.",
    );
  });
});
