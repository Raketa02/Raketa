import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { STRIPE_PAGES } from './suite';

/**
 * **Connect payments** (#562, the screens B2): the setup checklist's first step sends the club
 * to Stripe's hosted pages and back to Overview, and says where Stripe has it: *not started*,
 * *Stripe needs more details* (with *Continue with Stripe*), or *ready*.
 */

function payments(page: Page) {
  return page
    .getByRole('list', { name: 'Setup checklist' })
    .getByRole('listitem')
    .filter({ has: page.getByRole('heading', { name: 'Connect payments' }) });
}

test.describe('Connect payments', () => {
  test('a club not started connects with Stripe: off to its pages, and back to Overview', async ({
    page,
    stub,
    club,
  }) => {
    await signIn(page);
    const row = payments(page);
    await expect(row.locator('[data-state]')).toHaveText('not started');

    await row.getByRole('button', { name: 'Connect with Stripe' }).click();
    await expect(page.getByRole('heading', { name: 'Set up payments with Stripe' })).toBeVisible();
    expect(stub.requests('post', '/api/v1/club/payments/onboarding-link')).toHaveLength(1);
    expect(stub.stripePages).toEqual(club.rakieta.links);

    // The club gave Stripe what it had, and Stripe wants more.
    club.rakieta.payments = 'NEEDS_DETAILS';
    await page.getByRole('link', { name: 'Return to Rakieta' }).click();
    await expect(page).toHaveURL(/\/overview$/);
    await expect(row.locator('[data-state]')).toHaveText('Stripe needs more details');
    await expect(row.getByRole('button')).toHaveText('Continue with Stripe');
  });

  test('Stripe needs more details: Continue with Stripe opens a fresh link', async ({
    page,
    stub,
    club,
  }) => {
    club.rakieta.payments = 'NEEDS_DETAILS';
    club.rakieta.links.push(`${STRIPE_PAGES}/spent`);
    await signIn(page);
    const row = payments(page);
    await expect(row.locator('[data-state]')).toHaveText('Stripe needs more details');

    await row.getByRole('button', { name: 'Continue with Stripe' }).click();
    await expect(page.getByRole('heading', { name: 'Set up payments with Stripe' })).toBeVisible();
    expect(stub.requests('post', '/api/v1/club/payments/onboarding-link')).toHaveLength(1);
    expect(stub.stripePages).toEqual([club.rakieta.links[1]]);
  });

  test('ready: ticked, with nothing left to do', async ({ page, club }) => {
    club.rakieta.payments = 'READY';
    await signIn(page);
    const row = payments(page);
    await expect(row.locator('[data-state]')).toHaveText('ready ✓');
    await expect(row.getByRole('button')).toHaveCount(0);
    await expect(row.getByRole('link')).toHaveCount(0);
  });

  test('a Stripe the backend could not reach is said in the row, and the button stays', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await signIn(page);
    stub.on('post', '/api/v1/club/payments/onboarding-link', () => ({
      status: 503,
      body: refusal('payments_unavailable'),
    }));
    const row = payments(page);
    await row.getByRole('button', { name: 'Connect with Stripe' }).click();

    await expect(row.getByRole('alert')).toHaveText(
      "We couldn't reach Stripe. Try again in a moment.",
    );
    await expect(page).toHaveURL(/\/overview$/);
    await expect(row.getByRole('button', { name: 'Connect with Stripe' })).toBeEnabled();
  });

  test('Stripe saying the account is ready as the desk presses ticks the step', async ({
    page,
    stub,
    club,
  }) => {
    await signIn(page);
    // Every call reads the account as Stripe has it, before its notice arrives (#537).
    stub.on('post', '/api/v1/club/payments/onboarding-link', () => {
      club.rakieta.payments = 'READY';
      return { status: 409, body: refusal('payments_already_connected') };
    });
    const row = payments(page);
    await row.getByRole('button', { name: 'Connect with Stripe' }).click();

    await expect(row.locator('[data-state]')).toHaveText('ready ✓');
    await expect(row.getByRole('alert')).toHaveCount(0);
  });
});

/**
 * **`/payments/continue`**: where Stripe sends a desk whose link was spent or went stale, and
 * where the email *Stripe needs something from you* points. It asks for a fresh link and
 * follows it.
 */
test.describe('Continuing with Stripe from a link', () => {
  test('asks for a fresh link to Stripe’s pages, and follows it', async ({ page, stub, club }) => {
    club.rakieta.payments = 'NEEDS_DETAILS';
    await signIn(page);

    await page.goto('/payments/continue');
    await expect(page.getByRole('heading', { name: 'Set up payments with Stripe' })).toBeVisible();
    expect(stub.requests('post', '/api/v1/club/payments/onboarding-link')).toHaveLength(1);
    expect(stub.stripePages).toEqual(club.rakieta.links);
  });

  test('an account Stripe says is ready lands on Overview, ticked', async ({ page, club }) => {
    await signIn(page);
    club.rakieta.payments = 'READY';

    await page.goto('/payments/continue');
    await expect(page).toHaveURL(/\/overview$/);
    await expect(payments(page).locator('[data-state]')).toHaveText('ready ✓');
  });

  test('a Stripe that could not be reached leaves the desk on Overview, told so', async ({
    page,
    stub,
    club,
  }) => {
    club.rakieta.payments = 'NEEDS_DETAILS';
    await signIn(page);
    stub.on('post', '/api/v1/club/payments/onboarding-link', () => ({
      status: 503,
      body: refusal('payments_unavailable'),
    }));

    await page.goto('/payments/continue');
    await expect(page).toHaveURL(/\/overview\?notice=stripe-failed$/);
    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "We couldn't open Stripe's pages just now. Try again in a moment.",
    );
    await expect(payments(page).getByRole('button')).toHaveText('Continue with Stripe');
  });

  test('a browser not signed in signs in first, and nothing is asked of Stripe', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await page.goto('/payments/continue');
    await expect(page).toHaveURL(/\/sign-in$/);
    expect(stub.requests('post', '/api/v1/club/payments/onboarding-link')).toHaveLength(0);
  });
});
