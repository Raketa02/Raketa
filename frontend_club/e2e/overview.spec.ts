import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { booking } from './stub/bookings';
import { dayFromToday } from './stub/clock';
import { court, week } from './stub/courts';

/**
 * **Overview** (#561, #674, the screens B2): the setup checklist's four steps until the club is
 * live, each with its state and the one button that does it; then, once, *You're live*, the
 * checklist is gone, and Overview says the club is live on Rakieta, with the way to today's
 * Bookings. Connecting payments has its own spec, `connect-payments.spec.ts` (#562).
 */

const TOLD_LIVE_COOKIE = 'raketa_club_told_live';

function checklist(page: Page) {
  return page.getByRole('list', { name: 'Setup checklist' }).getByRole('listitem');
}

function step(page: Page, title: string) {
  return checklist(page).filter({ has: page.getByRole('heading', { name: title }) });
}

test.describe('Overview', () => {
  test('a new club sees the four steps, what each is waiting on, and the next one to take', async ({
    page,
    club,
  }) => {
    void club;
    await signIn(page);

    await expect(
      page.getByRole('heading', { name: 'Before your courts can be booked' }),
    ).toBeVisible();
    await expect(
      page.getByText("Your courts reach players' games once all four are done."),
    ).toBeVisible();
    // Every club works one way, so there is no way to choose (Q121).
    await expect(checklist(page).getByRole('heading')).toHaveText([
      'Connect payments',
      'Add your courts',
      'Set hours and prices',
      'Check the settings',
    ]);
    // Connecting payments comes first, so its button is the page's one primary button. The
    // settings wait for nothing.
    await expect(checklist(page).locator('[data-state]')).toHaveText([
      'not started',
      'to do',
      'locked',
      'to do',
    ]);

    await expect(page.getByRole('region', { name: 'Live on Rakieta' })).toHaveCount(0);

    await expect(step(page, 'Connect payments').getByRole('button')).toHaveText(
      'Connect with Stripe',
    );
    await expect(step(page, 'Set hours and prices').getByRole('link')).toHaveCount(0);
    await expect(step(page, 'Set hours and prices')).toContainText('Once you add a court.');
    await expect(step(page, 'Check the settings')).toContainText(
      'The release lead and the cut-off; then confirm them.',
    );

    await expect(step(page, 'Add your courts').getByRole('link')).toHaveAttribute(
      'href',
      '/courts',
    );
    const settings = step(page, 'Check the settings').getByRole('link');
    await expect(settings).toHaveText('Check the settings');
    await expect(settings).toHaveAttribute('href', '/rakieta-settings');
    await settings.click();
    await expect(page.getByRole('heading', { name: 'Rakieta settings', level: 1 })).toBeVisible();
  });

  test('steps done are ticked, and the first left to do is next', async ({ page, club }) => {
    club.raketa.payments = 'READY';
    club.raketa.courts = [court({ name: 'Court 1', sport: 'PADEL', hours: week([1], 17, 19) })];
    await signIn(page);

    await expect(checklist(page).locator('[data-state]')).toHaveText([
      'ready ✓',
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
      '/rakieta-settings',
    );
    await expect(page.getByText("You're live")).toBeHidden();
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
    await expect(checklist(page)).toHaveCount(4);
    await expect(page.getByRole('region', { name: 'Live on Rakieta' })).toHaveCount(0);
    await expect(step(page, 'Connect payments').locator('[data-state]')).toHaveText(
      'Stripe needs more details',
    );
    await expect(step(page, 'Connect payments').getByRole('button')).toHaveText(
      'Continue with Stripe',
    );
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
    await expect(checklist(page)).toHaveCount(4);
  });

  test("a live club is told it is live on Rakieta, with the way to today's Bookings", async ({
    page,
    club,
  }) => {
    club.raketa.ready();
    const padel = club.raketa.courts[0];
    if (padel === undefined) throw new Error('ready() seats a court');
    club.bookings.add(booking({ court: padel, day: dayFromToday(0), hour: 7 }));
    await signIn(page);

    const live = page.getByRole('region', { name: 'Live on Rakieta' });
    await expect(live).toContainText(
      'Every game booked on your courts through Rakieta is in Bookings, a day at a time.',
    );
    // Nothing waits for the club's answer any more (Q121).
    await expect(page.getByText('Waiting for your answer')).toHaveCount(0);
    await expect(page.getByRole('timer')).toHaveCount(0);

    // Said once, *You're live* goes; the line that the club is live stays.
    await page.reload();
    await expect(page.getByText("You're live")).toBeHidden();
    const today = live.getByRole('link', { name: 'Today’s bookings' });
    await expect(today).toHaveAttribute('href', '/bookings');
    await today.click();
    await expect(page.getByRole('heading', { name: 'Bookings', level: 1 })).toBeVisible();
    await expect(page.getByRole('heading', { name: /^Today · / })).toBeVisible();
    await expect(page.getByRole('rowheader')).toHaveText([/07:00–08:00\s*Court 1/]);
  });
});
