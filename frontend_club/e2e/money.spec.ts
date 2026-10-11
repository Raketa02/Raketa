import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { booking } from './stub/bookings';
import { atClubHour, dayFromToday } from './stub/clock';
import { court } from './stub/courts';
import { moneyRow, payout } from './stub/money';

/**
 * **Money** (#562, the screens B7): a month of the club's bookings' money, booking by booking,
 * with the month's totals at the top; its payouts, as Stripe has them; and a way to its own
 * Stripe dashboard.
 */

const PADEL = court({ name: 'Court 1', sport: 'PADEL' });
const TENNIS = court({ name: 'Kort 2', sport: 'TENNIS' });

function bookings(page: Page) {
  return page.getByRole('region', { name: /^March 2026$/ });
}

/** This month at the club, `2026-10`, and the one before it. */
function thisAndLastMonth(): { now: string; last: string } {
  const now = dayFromToday(0).slice(0, 7);
  const [year = 0, month = 1] = now.split('-').map(Number);
  const last = month === 1 ? `${year - 1}-12` : `${year}-${String(month - 1).padStart(2, '0')}`;
  return { now, last };
}

/** *October 2026*: a month as the page names it, written by the browser's own calendar. */
function named(month: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${month}-15T12:00:00Z`));
}

test.describe('Money', () => {
  test("opens from the bar, and a month's bookings show their money under the month's totals", async ({
    page,
    stub,
    club,
  }) => {
    club.money.add(
      moneyRow({
        court: TENNIS,
        day: '2026-03-14',
        hour: 9,
        collected_grosze: 80_00,
        card_fees_grosze: 3_70,
        paid_out: true,
      }),
    );
    club.money.add(moneyRow({ court: PADEL, day: '2026-03-02', hour: 19, paid_out: true }));
    // Another month's game is not this month's money.
    club.money.add(moneyRow({ court: PADEL, day: '2026-04-01', hour: 19 }));
    await signIn(page);

    const bar = page.getByRole('navigation', { name: 'Club website' });
    await bar.getByRole('link', { name: 'Money' }).click();
    await expect(page.getByRole('heading', { name: 'Money', level: 1 })).toBeVisible();
    await expect(bar.getByRole('link', { name: 'Money' })).toHaveAttribute('aria-current', 'page');

    await page.goto('/money?month=2026-03');
    const month = bookings(page);
    await expect(month.getByRole('heading', { name: 'March 2026' })).toBeVisible();
    expect(stub.requests('get', '/api/v1/club/money').at(-1)?.query).toEqual({
      month: '2026-03',
    });

    await expect(month.getByRole('definition')).toHaveText([
      '220 zł',
      '0 zł',
      '9,70 zł',
      '210,30 zł',
    ]);
    await expect(month.getByRole('term')).toHaveText(['Collected', 'Refunded', 'Card fees', 'Net']);

    const rows = month.getByRole('row');
    // The heads, then soonest first.
    await expect(rows).toHaveCount(3);
    await expect(rows.nth(1).getByRole('cell')).toHaveText([
      'Court 1 Padel · Played',
      '140 zł',
      '0 zł',
      '6 zł',
      '134 zł',
      'Paid out ✓',
    ]);
    await expect(rows.nth(1).getByRole('rowheader')).toHaveText('Mon 2 Mar · 19:00');
    await expect(rows.nth(2).getByRole('rowheader')).toHaveText('Sat 14 Mar · 09:00');
    await expect(rows.nth(2).getByRole('cell')).toHaveText([
      'Kort 2 Tennis · Played',
      '80 zł',
      '0 zł',
      '3,70 zł',
      '76,30 zł',
      'Paid out ✓',
    ]);
  });

  test('this month comes first, and the arrows and the month box go to another', async ({
    page,
    stub,
    club,
  }) => {
    const { now, last } = thisAndLastMonth();
    club.money.add(moneyRow({ court: PADEL, day: '2026-03-02', hour: 19 }));
    await signIn(page);
    await page.goto('/money');
    const months = page.getByRole('navigation', { name: 'Month' });

    // The backend says which month this is.
    await expect(page.getByRole('heading', { name: named(now), level: 2 })).toBeVisible();
    expect(stub.requests('get', '/api/v1/club/money').at(-1)?.query).toEqual({});
    await expect(months.getByRole('link', { name: 'This month' })).toHaveCount(0);

    await months.getByRole('link', { name: 'Previous month' }).click();
    await expect(page.getByRole('heading', { name: named(last), level: 2 })).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`/money\\?month=${last}$`));
    await months.getByRole('link', { name: 'This month' }).click();
    await expect(page.getByRole('heading', { name: named(now), level: 2 })).toBeVisible();
    await expect(page).toHaveURL(/\/money$/);

    await page.getByLabel('Go to a month').fill('2026-03');
    await page.getByRole('button', { name: 'Show' }).click();
    await expect(page).toHaveURL(/\/money\?month=2026-03$/);
    await expect(bookings(page).getByRole('row')).toHaveCount(2);

    await months.getByRole('link', { name: 'Next month' }).click();
    await expect(page.getByRole('heading', { name: 'April 2026', level: 2 })).toBeVisible();
    expect(stub.requests('get', '/api/v1/club/money').at(-1)?.query).toEqual({
      month: '2026-04',
    });
  });

  test('a month nobody paid in says so, and a month the address cannot read is this one', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await signIn(page);
    await page.goto('/money?month=2026-02');
    const month = page.getByRole('region', { name: 'February 2026' });
    await expect(month).toContainText('No Raketa booking took money in February 2026.');
    await expect(month.getByRole('table')).toHaveCount(0);
    await expect(month.getByRole('definition')).toHaveText(['0 zł', '0 zł', '0 zł', '0 zł']);

    await page.goto('/money?month=2026-13');
    await expect(
      page.getByRole('heading', { name: named(thisAndLastMonth().now), level: 2 }),
    ).toBeVisible();
    expect(stub.requests('get', '/api/v1/club/money').at(-1)?.query).toEqual({});
  });

  test('a game whose shares are held has collected nothing; at its cut-off they are taken, and its card fees are not yet known until Stripe says', async ({
    page,
    club,
  }) => {
    club.raketa.courts = [PADEL];
    // A game two days ahead: its cut-off, a day before it, is still ahead.
    const day = dayFromToday(2);
    const month = day.slice(0, 7);
    const game = club.bookings.add(
      booking({
        court: PADEL,
        day,
        hour: 19,
        money: { price_grosze: 160_00, collected_grosze: 0, refunded_grosze: 0 },
      }),
    );
    await signIn(page);
    const theGame = () =>
      page
        .getByRole('row')
        .filter({ has: page.getByRole('rowheader').filter({ hasText: '19:00–20:00' }) });
    const theMonth = () => page.getByRole('region', { name: named(month) });

    await page.goto(`/bookings?date=${day}`);
    await expect(theGame().getByRole('cell').nth(1).getByRole('listitem')).toHaveText([
      /held$/,
      /held$/,
      /held$/,
      /held$/,
    ]);
    await expect(theGame().getByRole('cell').nth(3)).toHaveText(
      /Price\s*160 zł\s*Collected\s*0 zł\s*Refunded\s*0 zł/,
    );
    // A share only held is no money yet.
    await page.goto(`/money?month=${month}`);
    await expect(theMonth()).toContainText(`No Raketa booking took money in ${named(month)}.`);
    await expect(theMonth().getByRole('definition')).toHaveText(['0 zł', '0 zł', '0 zł', '0 zł']);

    // The cut-off comes and takes the four shares. Stripe hasn't said its fees yet.
    club.bookings.passTheCutOff(game);
    const taken = club.money.add(
      moneyRow({
        court: PADEL,
        day,
        hour: 19,
        booking_id: game.booking_id,
        status: 'BOOKED',
        collected_grosze: 160_00,
        card_fees_grosze: null,
      }),
    );
    await page.goto(`/bookings?date=${day}`);
    await expect(theGame().getByRole('cell').nth(1).getByRole('listitem')).toHaveText([
      /taken$/,
      /taken$/,
      /taken$/,
      /taken$/,
    ]);
    await expect(theGame().getByRole('cell').nth(3)).toHaveText(
      /Price\s*160 zł\s*Collected\s*160 zł\s*Refunded\s*0 zł/,
    );
    await page.goto(`/money?month=${month}`);
    await expect(theMonth().getByRole('definition')).toHaveText([
      '160 zł',
      '0 zł',
      'Not yet known',
      'Not yet known',
    ]);
    await expect(theMonth().getByRole('row').nth(1).getByRole('cell')).toHaveText([
      'Court 1 Padel · Booked',
      '160 zł',
      '0 zł',
      'Not yet known',
      'Not yet known',
      'Not yet',
    ]);

    // Stripe says the fees it kept: the real ones, never an estimate.
    taken.card_fees_grosze = 6_40;
    await page.reload();
    await expect(theMonth().getByRole('definition')).toHaveText([
      '160 zł',
      '0 zł',
      '6,40 zł',
      '153,60 zł',
    ]);
    await expect(theMonth().getByRole('row').nth(1).getByRole('cell')).toHaveText([
      'Court 1 Padel · Booked',
      '160 zł',
      '0 zł',
      '6,40 zł',
      '153,60 zł',
      'Not yet',
    ]);
  });

  test('a refund that waits for its fee is not yet known, and so is what is the club’s', async ({
    page,
    club,
  }) => {
    club.money.add(moneyRow({ court: PADEL, day: '2026-03-02', hour: 19 }));
    club.money.add(moneyRow({ court: TENNIS, day: '2026-03-03', hour: 9, refunded_grosze: null }));
    await signIn(page);
    await page.goto('/money?month=2026-03');
    const month = bookings(page);
    await expect(month.getByRole('definition')).toHaveText([
      '280 zł',
      'Not yet known',
      '12 zł',
      'Not yet known',
    ]);
    await expect(month.getByRole('row').nth(2).getByRole('cell')).toHaveText([
      'Kort 2 Tennis · Played',
      '140 zł',
      'Not yet known',
      '6 zł',
      'Not yet known',
      'Not yet',
    ]);
  });

  test('a game given back whole leaves the club its card fees, said below nought', async ({
    page,
    club,
  }) => {
    club.money.add(
      moneyRow({
        court: PADEL,
        day: '2026-03-07',
        hour: 18,
        status: 'CALLED_OFF',
        refunded_grosze: 140_00,
      }),
    );
    await signIn(page);
    await page.goto('/money?month=2026-03');
    const month = bookings(page);
    await expect(month.getByRole('row').nth(1).getByRole('cell')).toHaveText([
      'Court 1 Padel · Called off',
      '140 zł',
      '140 zł',
      '6 zł',
      '−6 zł',
      'Not yet',
    ]);
    await expect(month.getByRole('definition').last()).toHaveText('−6 zł');
  });
});

test.describe('Payouts', () => {
  function payouts(page: Page) {
    return page.getByRole('region', { name: 'Payouts' });
  }

  test('newest first, each with the day it reaches the bank, its amount and where it stands', async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.payments = 'READY';
    const at = (day: string) => atClubHour(day, 12);
    club.money.payouts = [
      payout({ amount_grosze: 12_840_00, arrives_at: at('2026-03-03') }),
      payout({ amount_grosze: 210_30, arrives_at: at('2026-03-17'), status: 'PENDING' }),
      payout({ amount_grosze: 1_076_30, arrives_at: at('2026-03-10'), status: 'FAILED' }),
      payout({ amount_grosze: 90_00, arrives_at: at('2026-03-12'), status: 'IN_TRANSIT' }),
      payout({ amount_grosze: 45_50, arrives_at: at('2026-03-09'), status: 'CANCELLED' }),
    ];
    await signIn(page);
    await page.goto('/money');

    const rows = payouts(page).getByRole('row');
    await expect(rows).toHaveCount(6);
    await expect(rows.getByRole('rowheader')).toHaveText([
      'Tue 17 Mar',
      'Thu 12 Mar',
      'Tue 10 Mar',
      'Mon 9 Mar',
      'Tue 3 Mar',
    ]);
    await expect(rows.nth(1).getByRole('cell')).toHaveText(['210,30 zł', 'On its way']);
    await expect(rows.nth(2).getByRole('cell')).toHaveText(['90 zł', 'On its way']);
    await expect(rows.nth(3).getByRole('cell')).toHaveText([
      '1076,30 zł',
      'Your bank refused it Check your bank details in your Stripe dashboard.',
    ]);
    await expect(rows.nth(4).getByRole('cell')).toHaveText(['45,50 zł', 'Cancelled']);
    // Five figures and more are set in threes; four stay whole.
    await expect(rows.nth(5).getByRole('cell')).toHaveText(['12 840 zł', 'In your bank']);
    expect(stub.requests('get', '/api/v1/club/payouts')).toHaveLength(1);

    const dashboard = payouts(page).getByRole('link', { name: 'Open your Stripe dashboard' });
    await expect(dashboard).toHaveAttribute('href', 'https://dashboard.stripe.com');
    await expect(dashboard).toHaveAttribute('target', '_blank');
  });

  test('none yet, said so', async ({ page, club }) => {
    club.raketa.payments = 'READY';
    await signIn(page);
    await page.goto('/money');
    await expect(payouts(page)).toContainText('No payouts yet.');
    await expect(payouts(page).getByRole('table')).toHaveCount(0);
  });

  test('payouts Stripe could not give are said so, and the month is shown all the same', async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.payments = 'READY';
    club.money.add(moneyRow({ court: PADEL, day: '2026-03-02', hour: 19 }));
    stub.on('get', '/api/v1/club/payouts', () => ({
      status: 503,
      body: refusal('payments_unavailable'),
    }));
    await signIn(page);
    await page.goto('/money?month=2026-03');

    await expect(payouts(page).getByRole('alert')).toHaveText(
      "We couldn't reach Stripe for your payouts. Try again in a moment.",
    );
    await expect(bookings(page).getByRole('row')).toHaveCount(2);
  });

  test('a club that has not connected payments is sent to connect them, not to Stripe', async ({
    page,
    club,
  }) => {
    void club;
    await signIn(page);
    await page.goto('/money');
    await expect(
      payouts(page).getByRole('link', { name: 'Open your Stripe dashboard' }),
    ).toHaveCount(0);
    const connect = payouts(page).getByRole('link', { name: 'Connect payments on Overview' });
    await expect(connect).toHaveAttribute('href', '/overview');
  });

  test('Stripe still wanting details leaves the dashboard open to the club', async ({
    page,
    club,
  }) => {
    club.raketa.payments = 'NEEDS_DETAILS';
    await signIn(page);
    await page.goto('/money');
    await expect(
      payouts(page).getByRole('link', { name: 'Open your Stripe dashboard' }),
    ).toBeVisible();
  });
});
