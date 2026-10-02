import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { court, week } from './stub/courts';

/**
 * **Overview** (#561, the screens B2): the setup checklist until the club is live, each step
 * with its state and the one button that does it; then, once, *You're live*, and the checklist
 * is gone. Connecting payments is shown as pending until its own ticket (#562) opens it here.
 */

const TOLD_LIVE_COOKIE = 'raketa_club_told_live';

function checklist(page: Page) {
  return page.getByRole('list', { name: 'Setup checklist' }).getByRole('listitem');
}

function step(page: Page, title: string) {
  return checklist(page).filter({ has: page.getByRole('heading', { name: title }) });
}

test.describe('Overview', () => {
  test('a new club sees the five steps, what each is waiting on, and the next one to take', async ({
    page,
    club,
  }) => {
    void club;
    await signIn(page);

    await expect(
      page.getByRole('heading', { name: 'Before your courts can be booked' }),
    ).toBeVisible();
    await expect(checklist(page).getByRole('heading')).toHaveText([
      'Connect payments',
      'Choose how you work with Raketa',
      'Add your courts',
      'Set hours and prices',
      'Check the settings',
    ]);
    await expect(checklist(page).locator('[data-state]')).toHaveText([
      'pending',
      'next',
      'to do',
      'locked',
      'locked',
    ]);

    // Payments are connected from here with their own ticket: no button yet.
    await expect(step(page, 'Connect payments').getByRole('link')).toHaveCount(0);
    await expect(step(page, 'Set hours and prices').getByRole('link')).toHaveCount(0);
    await expect(step(page, 'Set hours and prices')).toContainText('Once you add a court.');
    await expect(step(page, 'Check the settings').getByRole('link')).toHaveCount(0);
    await expect(step(page, 'Check the settings')).toContainText(
      'Once you choose how you work with Raketa.',
    );

    const choose = step(page, 'Choose how you work with Raketa').getByRole('link');
    await expect(choose).toHaveText('Choose');
    await expect(choose).toHaveAttribute('href', '/raketa-settings');
    await expect(step(page, 'Add your courts').getByRole('link')).toHaveAttribute(
      'href',
      '/courts',
    );
    await choose.click();
    await expect(page.getByRole('heading', { name: 'Raketa settings', level: 1 })).toBeVisible();
  });

  test('steps done are ticked, and the first left to do is next', async ({ page, club }) => {
    club.raketa.payments = 'NEEDS_DETAILS';
    club.raketa.way = 'ON_REQUEST';
    club.raketa.courts = [court({ name: 'Court 1', sport: 'PADEL', hours: week([1], 17, 19) })];
    await signIn(page);

    await expect(checklist(page).locator('[data-state]')).toHaveText([
      'pending',
      'done ✓',
      'done ✓',
      'next',
      'to do',
    ]);
    await expect(step(page, 'Set hours and prices').getByRole('link')).toHaveAttribute(
      'href',
      '/courts#hours',
    );
    await expect(step(page, 'Check the settings').getByRole('link')).toHaveAttribute(
      'href',
      '/raketa-settings',
    );
    await expect(page.getByText("You're live")).toBeHidden();
  });

  test('payments a provider says are ready are ticked like any other step', async ({
    page,
    club,
  }) => {
    club.raketa.payments = 'READY';
    await signIn(page);
    await expect(step(page, 'Connect payments').locator('[data-state]')).toHaveText('done ✓');
  });

  test('a live club is told so once, and the checklist is gone', async ({
    page,
    context,
    club,
  }) => {
    club.raketa.ready();
    await signIn(page);

    await expect(page.getByRole('main').getByRole('status')).toHaveText(
      "You're live — your courts can now be booked through Raketa.",
    );
    await expect(page.getByRole('list', { name: 'Setup checklist' })).toHaveCount(0);
    await expect
      .poll(async () => (await context.cookies()).map((cookie) => cookie.name))
      .toContain(TOLD_LIVE_COOKIE);
    const seen = (await context.cookies()).find((cookie) => cookie.name === TOLD_LIVE_COOKIE);
    expect(seen).toMatchObject({ httpOnly: true, sameSite: 'Lax', path: '/' });

    await page.reload();
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
    await expect(page.getByText("You're live")).toBeHidden();
    await expect(page.getByRole('list', { name: 'Setup checklist' })).toHaveCount(0);
  });

  test('a club that stops being live gets its checklist back, and is told again when live', async ({
    page,
    context,
    club,
  }) => {
    club.raketa.ready();
    await signIn(page);
    await expect(page.getByText("You're live")).toBeVisible();
    await expect
      .poll(async () => (await context.cookies()).map((cookie) => cookie.name))
      .toContain(TOLD_LIVE_COOKIE);

    // Stripe wants more details: the club is not live until it has them.
    club.raketa.payments = 'NEEDS_DETAILS';
    await page.reload();
    await expect(checklist(page)).toHaveCount(5);
    await expect
      .poll(async () => (await context.cookies()).map((cookie) => cookie.name))
      .not.toContain(TOLD_LIVE_COOKIE);

    club.raketa.payments = 'READY';
    await page.reload();
    await expect(page.getByText("You're live")).toBeVisible();
  });

  test('a new password is still said over the checklist', async ({ page, club }) => {
    void club;
    await signIn(page);
    await page.goto('/overview?notice=password-set');
    await expect(page.getByRole('main').getByRole('status')).toHaveText(
      'New password set. Any other browser signed in as the club is signed out.',
    );
    await expect(checklist(page)).toHaveCount(5);
  });
});
