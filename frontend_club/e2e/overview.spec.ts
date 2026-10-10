import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { booking } from './stub/bookings';
import { fromNow } from './stub/club';
import { dayFromToday } from './stub/clock';
import { court, week } from './stub/courts';

/**
 * **Overview** (#561, #563, the screens B2): the setup checklist until the club is live, each
 * step with its state and the one button that does it; then, once, *You're live*, the checklist
 * is gone, and Overview shows only what waits for the club's answer. Connecting payments has its
 * own spec, `connect-payments.spec.ts` (#562).
 */

const MINUTE_MS = 60_000;

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
    // Connecting payments comes first, so its button is the page's one primary button.
    await expect(checklist(page).locator('[data-state]')).toHaveText([
      'not started',
      'to do',
      'to do',
      'locked',
      'locked',
    ]);

    await expect(page.getByRole('region', { name: 'Waiting for your answer' })).toHaveCount(0);

    await expect(step(page, 'Connect payments').getByRole('button')).toHaveText(
      'Connect with Stripe',
    );
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
    club.raketa.payments = 'READY';
    club.raketa.way = 'ON_REQUEST';
    club.raketa.courts = [court({ name: 'Court 1', sport: 'PADEL', hours: week([1], 17, 19) })];
    await signIn(page);

    await expect(checklist(page).locator('[data-state]')).toHaveText([
      'ready ✓',
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
    await expect(checklist(page)).toHaveCount(5);
  });

  test('a live club with nothing waiting is told so', async ({ page, club }) => {
    club.raketa.ready();
    const padel = club.raketa.courts[0];
    if (padel === undefined) throw new Error('ready() seats a court');
    club.bookings.add(booking({ court: padel, day: dayFromToday(1), hour: 19 }));
    // Accepted, and waiting on one player's payment: the desk has answered it (Q112).
    club.bookings.add(
      booking({ court: padel, day: dayFromToday(1), hour: 20, stage: 'WAITING_FOR_A_PAYMENT' }),
    );
    await signIn(page);

    const waiting = page.getByRole('region', { name: 'Waiting for your answer' });
    await expect(waiting).toContainText('Nothing is waiting for you.');
    await expect(waiting.getByRole('listitem')).toHaveCount(0);
    await expect(page.getByText('Nothing to show here yet.')).toHaveCount(0);
    await expect(
      page.getByRole('navigation', { name: 'Club website' }).getByRole('link', {
        name: 'Bookings',
        exact: true,
      }),
    ).toBeVisible();
    // What a request left unanswered comes to, in the players' own words (Q105).
    await expect(waiting).toContainText(
      'a request not answered in time is called off: the players read “Ogrody 33 didn’t answer in time”.',
    );
  });

  test('a live club sees only what waits for its answer, and answers it there', async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.ready();
    const padel = club.raketa.courts[0];
    if (padel === undefined) throw new Error('ready() seats a court');
    club.bookings.add(booking({ court: padel, day: dayFromToday(1), hour: 18 }));
    const later = club.bookings.add(
      booking({
        court: padel,
        day: dayFromToday(2),
        hour: 20,
        stage: 'WAITING_FOR_YOU',
        kind: 'FOR_FUN',
        answer_by: fromNow(28 * MINUTE_MS),
      }),
    );
    const sooner = club.bookings.add(
      booking({
        court: padel,
        day: dayFromToday(1),
        hour: 19,
        stage: 'WAITING_FOR_YOU',
        answer_by: fromNow(12 * MINUTE_MS),
      }),
    );
    await signIn(page);
    const bar = page.getByRole('navigation', { name: 'Club website' });
    await expect(
      bar.getByRole('link', { name: 'Bookings, 2 waiting for your answer' }),
    ).toBeVisible();

    const waiting = page.getByRole('region', { name: 'Waiting for your answer' });
    const requests = waiting.getByRole('listitem');
    // The one due first, first; booked games are not here.
    await expect(requests).toHaveCount(2);
    await expect(requests.first()).toContainText('19:00–20:00 · Court 1');
    await expect(requests.first()).toContainText('Padel · Competitive');
    await expect(requests.first()).toContainText(
      'Anna Nowak, Piotr Sikora, Kasia Wiśniewska, Marek Zając',
    );
    await expect(requests.first()).toContainText('140 zł · 35 zł each');
    await expect(requests.first().getByRole('timer')).toHaveText(/^1[12]:\d\d left to answer$/);
    await expect(requests.last()).toContainText('20:00–21:00 · Court 1');
    await expect(requests.last()).toContainText('Padel · Friendly');
    await expect(requests.last().getByRole('timer')).toHaveText(/^2[78]:\d\d left to answer$/);

    await requests
      .first()
      .getByRole('button', { name: /^Accept/ })
      .click();
    await expect(page.getByRole('main').getByRole('status').last()).toHaveText(
      /^The 19:00 game on .+ is booked on Court 1\. Everybody paid\.$/,
    );
    await expect(requests).toHaveCount(1);
    await expect(
      bar.getByRole('link', { name: 'Bookings, 1 waiting for your answer' }),
    ).toBeVisible();

    await requests
      .first()
      .getByRole('button', { name: /^Refuse/ })
      .click();
    const dialog = page.getByRole('dialog', { name: /^Refuse the 20:00 game on / });
    await dialog.getByRole('button', { name: 'Refuse', exact: true }).click();
    await expect(waiting).toContainText('Nothing is waiting for you.');
    await expect(bar.getByRole('link', { name: 'Bookings', exact: true })).toBeVisible();
    expect(
      stub.requests('post', '/api/v1/club/bookings/{booking_id}/acceptance').map((r) => r.params),
    ).toEqual([{ booking_id: sooner.booking_id }]);
    expect(
      stub.requests('post', '/api/v1/club/bookings/{booking_id}/refusal').map((r) => r.params),
    ).toEqual([{ booking_id: later.booking_id }]);
  });
});
