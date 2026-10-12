import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { booking } from './stub/bookings';
import { fromNow } from './stub/club';
import { clubTime, dayFromToday } from './stub/clock';
import { court, week } from './stub/courts';

/**
 * **Bookings** (#563, #674, the screens B4, the mechanics §16.7, §16.9 and §16.16): every Raketa
 * booking at the club, one day at a time, with its players, its status, its money and the group
 * it came from, and the games the club moves or cancels. No club confirms a game (Q121), so
 * nothing on the page waits for the desk's answer.
 */

const EVERY_DAY = [1, 2, 3, 4, 5, 6, 7];
const MINUTE_MS = 60_000;
const HOUR_MS = 60 * MINUTE_MS;

/** The row a booking's hour heads. */
function rowAt(page: Page, hours: string) {
  return page
    .getByRole('row')
    .filter({ has: page.getByRole('rowheader').filter({ hasText: hours }) });
}

async function openDay(page: Page, day: string) {
  await signIn(page);
  await page.goto(`/bookings?date=${day}`);
  await expect(page.getByRole('heading', { name: 'Bookings', level: 1 })).toBeVisible();
}

test.describe('Bookings', () => {
  test('a day lists each game: its hour and court, sport and kind, players and their shares, status, money and group', async ({
    page,
    club,
  }) => {
    const padel = court({ name: 'Court 1', sport: 'PADEL', hours: week(EVERY_DAY, 7, 23) });
    const tennis = court({
      name: 'Kort centralny',
      sport: 'TENNIS',
      hours: week(EVERY_DAY, 7, 23),
    });
    club.raketa.courts = [padel, tennis];
    const day = dayFromToday(2);
    club.bookings.add(booking({ court: padel, day, hour: 19 }));
    club.bookings.add(
      booking({
        court: tennis,
        day,
        hour: 18,
        kind: 'FOR_FUN',
        stage: 'SEAT_OPEN',
        // Its cut-off has passed: the shares are taken, and a leaver's refund less the fee kept
        // on their payment waits for Stripe to say the fee (#641).
        cut_off: fromNow(-HOUR_MS),
        booked_from: { group_id: crypto.randomUUID(), name: 'Padel po pracy', official: false },
        money: { price_grosze: 90_00, collected_grosze: 90_00, refunded_grosze: null },
      }),
    );
    club.bookings.add(booking({ court: padel, day: dayFromToday(3), hour: 19 }));

    await openDay(page, day);

    // Soonest first, and only that day's.
    await expect(page.getByRole('rowheader')).toHaveText([
      /18:00–19:00\s*Kort centralny/,
      /19:00–20:00\s*Court 1/,
    ]);

    const seatOpen = rowAt(page, '18:00–19:00');
    await expect(seatOpen.getByRole('cell').nth(0)).toHaveText('Tennis · Friendly');
    await expect(seatOpen.getByRole('cell').nth(1).getByRole('listitem')).toHaveText([
      /Anna Nowak\s*taken$/,
      'Open seat',
    ]);
    await expect(seatOpen.getByRole('cell').nth(2)).toHaveText('Seat open');
    await expect(seatOpen.getByRole('cell').nth(3)).toHaveText(
      /Price\s*90 zł\s*Collected\s*90 zł\s*Refunded\s*Not yet known/,
    );
    await expect(seatOpen.getByRole('cell').nth(4)).toHaveText(/Padel po pracy\s*Player group/);

    // Its cut-off is a day before it, still ahead: every share is held, and nothing collected.
    const booked = rowAt(page, '19:00–20:00');
    await expect(booked.getByRole('cell').nth(0)).toHaveText('Padel · Competitive');
    await expect(booked.getByRole('cell').nth(1).getByRole('listitem')).toHaveText([
      /Anna Nowak\s*held$/,
      /Piotr Sikora\s*held$/,
      /Kasia Wiśniewska\s*held$/,
      /Marek Zając\s*held$/,
    ]);
    await expect(booked.getByRole('cell').nth(2)).toHaveText('Booked');
    await expect(booked.getByRole('cell').nth(3)).toHaveText(
      /Price\s*140 zł\s*Collected\s*0 zł\s*Refunded\s*0 zł/,
    );
    await expect(booked.getByRole('cell').nth(4)).toHaveText(/Ogrody 33 Club\s*Official group/);
  });

  test('Bookings is in the top bar, and opens on today', async ({ page, stub, club }) => {
    const padel = court({ name: 'Court 1', sport: 'PADEL' });
    club.raketa.courts = [padel];
    club.bookings.add(booking({ court: padel, day: dayFromToday(0), hour: 7 }));
    await signIn(page);

    const pages = page.getByRole('navigation', { name: 'Club website' });
    await pages.getByRole('link', { name: 'Bookings' }).click();

    await expect(page).toHaveURL(/\/bookings$/);
    await expect(page.getByRole('heading', { name: 'Bookings', level: 1 })).toBeVisible();
    await expect(pages.getByRole('link', { name: 'Bookings' })).toHaveAttribute(
      'aria-current',
      'page',
    );
    await expect(page.getByRole('heading', { name: /^Today · / })).toBeVisible();
    await expect(page.getByRole('rowheader')).toHaveText([/07:00–08:00\s*Court 1/]);
    expect(stub.requests('get', '/api/v1/club/bookings').at(-1)?.query).toEqual({
      filter: 'ALL',
    });
  });

  test('the desk checks nobody in: Bookings has no Check in, and its old address finds nothing', async ({
    page,
    club,
  }) => {
    const padel = court({ name: 'Court 1', sport: 'PADEL' });
    club.raketa.courts = [padel];
    club.bookings.add(booking({ court: padel, day: dayFromToday(0), hour: 7 }));
    await openDay(page, dayFromToday(0));
    await expect(page.getByRole('rowheader')).toHaveText([/07:00–08:00\s*Court 1/]);
    await expect(page.getByRole('link', { name: 'Check in' })).toHaveCount(0);

    const old = await page.goto('/bookings/check-in');
    expect(old?.status()).toBe(404);
    await expect(page.getByRole('heading', { name: 'Nothing at this address' })).toBeVisible();
  });

  test('a called-off game says why, and a nameless player is still a seat', async ({
    page,
    club,
  }) => {
    const padel = court({ name: 'Court 1', sport: 'PADEL' });
    club.raketa.courts = [padel];
    const day = dayFromToday(1);
    club.bookings.add(
      booking({
        court: padel,
        day,
        hour: 10,
        stage: 'CALLED_OFF',
        called_off_reason: 'CANCELLED_BY_THE_CLUB',
        cancel_reason: 'DOUBLE_BOOKING',
        booked_from: null,
      }),
    );
    club.bookings.add(
      booking({
        court: padel,
        day,
        hour: 11,
        stage: 'CALLED_OFF',
        called_off_reason: 'SHORT_AT_THE_CUT_OFF',
      }),
    );
    const nameless = club.bookings.add(
      booking({ court: padel, day, hour: 12, cut_off: fromNow(-HOUR_MS) }),
    );
    nameless.players = nameless.players.map((player, index) =>
      index === 3 ? { ...player, name: null } : player,
    );

    await openDay(page, day);

    await expect(page.getByRole('rowheader')).toHaveCount(3);
    await expect(rowAt(page, '10:00–11:00').getByRole('cell').nth(2)).toHaveText(
      /Called off\s*Cancelled by you · Double booking/,
    );
    await expect(rowAt(page, '10:00–11:00').getByRole('cell').nth(4)).toHaveText(
      'A group that’s gone',
    );
    await expect(rowAt(page, '11:00–12:00').getByRole('cell').nth(2)).toHaveText(
      /Called off\s*Short at the cut-off/,
    );
    await expect(
      rowAt(page, '12:00–13:00').getByRole('cell').nth(1).getByRole('listitem').last(),
    ).toHaveText(/A player\s*taken/);
  });

  test('‹ and › walk the days, the date box opens any, and Today comes back', async ({
    page,
    stub,
    club,
  }) => {
    const padel = court({ name: 'Court 1', sport: 'PADEL' });
    club.raketa.courts = [padel];
    club.bookings.add(booking({ court: padel, day: dayFromToday(1), hour: 19 }));
    const day = page.getByRole('navigation', { name: 'Day' });
    const lastQuery = () => stub.requests('get', '/api/v1/club/bookings').at(-1)?.query;
    await signIn(page);
    await page.goto('/bookings');

    await expect(day.getByRole('heading', { name: /^Today · / })).toBeVisible();
    await expect(page.getByText('No Raketa bookings on this day.')).toBeVisible();
    await expect(day.getByRole('link', { name: 'Today', exact: true })).toHaveCount(0);

    await day.getByRole('link', { name: 'Next day' }).click();
    await expect(day.getByRole('heading', { name: /^Tomorrow · / })).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`/bookings\\?date=${dayFromToday(1)}$`));
    await expect(page.getByRole('rowheader')).toHaveText([/19:00–20:00/]);
    expect(lastQuery()).toEqual({ date: dayFromToday(1), filter: 'ALL' });

    await day.getByRole('link', { name: 'Next day' }).click();
    await expect(page).toHaveURL(new RegExp(`date=${dayFromToday(2)}$`));
    await expect(day.getByRole('heading', { level: 2 })).toHaveText(/^\w{3} \d{1,2} \w{3}$/);

    await page.getByLabel('Go to a day').fill(dayFromToday(-1));
    await page.getByRole('button', { name: 'Show' }).click();
    await expect(day.getByRole('heading', { name: /^Yesterday · / })).toBeVisible();
    await expect(page.getByLabel('Go to a day')).toHaveValue(dayFromToday(-1));

    await day.getByRole('link', { name: 'Previous day' }).click();
    await expect(page).toHaveURL(new RegExp(`date=${dayFromToday(-2)}$`));
    await day.getByRole('link', { name: 'Today', exact: true }).click();
    await expect(page).toHaveURL(/\/bookings$/);
    await expect(day.getByRole('heading', { name: /^Today · / })).toBeVisible();
    expect(lastQuery()).toEqual({ filter: 'ALL' });
  });

  test('an address the page cannot read opens today, all of it', async ({ page, stub, club }) => {
    void club;
    await signIn(page);
    // `waiting` was *Waiting for you*'s word, which went with On request (Q121).
    for (const filter of ['everything', 'waiting']) {
      await page.goto(`/bookings?date=2026-02-30&filter=${filter}&booking=nobody`);
      await expect(
        page.getByRole('navigation', { name: 'Day' }).getByRole('heading', { name: /^Today · / }),
      ).toBeVisible();
      await expect(
        page
          .getByRole('navigation', { name: 'Filter bookings' })
          .getByRole('link', { name: /^All/ }),
      ).toHaveAttribute('aria-current', 'true');
      expect(stub.requests('get', '/api/v1/club/bookings').at(-1)?.query).toEqual({
        filter: 'ALL',
      });
    }
  });

  test('the filters narrow the day, each with the whole day’s count, and stay as the day changes', async ({
    page,
    stub,
    club,
  }) => {
    const padel = court({ name: 'Court 1', sport: 'PADEL' });
    club.raketa.courts = [padel];
    const day = dayFromToday(2);
    club.bookings.add(booking({ court: padel, day, hour: 18 }));
    club.bookings.add(booking({ court: padel, day, hour: 19, stage: 'SEAT_OPEN' }));
    club.bookings.add(
      booking({
        court: padel,
        day,
        hour: 21,
        stage: 'CALLED_OFF',
        called_off_reason: 'SHORT_AT_THE_CUT_OFF',
      }),
    );
    await openDay(page, day);
    const filters = page.getByRole('navigation', { name: 'Filter bookings' });

    // Nothing waits for the desk's answer (Q121): there is no *Waiting for you*.
    await expect(filters.getByRole('link')).toHaveText(['All 3', 'Seat open 1', 'Called off 1']);
    await expect(filters.getByRole('link', { name: 'All 3' })).toHaveAttribute(
      'aria-current',
      'true',
    );

    await filters.getByRole('link', { name: /^Seat open/ }).click();
    await expect(page).toHaveURL(new RegExp(`date=${day}&filter=seat-open$`));
    await expect(page.getByRole('rowheader')).toHaveText([/19:00–20:00/]);
    await expect(filters.getByRole('link', { name: /^Seat open/ })).toHaveAttribute(
      'aria-current',
      'true',
    );
    expect(stub.requests('get', '/api/v1/club/bookings').at(-1)?.query).toEqual({
      date: day,
      filter: 'SEAT_OPEN',
    });

    await filters.getByRole('link', { name: /^Called off/ }).click();
    await expect(page).toHaveURL(new RegExp(`date=${day}&filter=called-off$`));
    await expect(page.getByRole('rowheader')).toHaveText([/21:00–22:00/]);

    await page
      .getByRole('navigation', { name: 'Day' })
      .getByRole('link', { name: 'Next day' })
      .click();
    await expect(page).toHaveURL(new RegExp(`date=${dayFromToday(3)}&filter=called-off$`));
    await expect(page.getByText('No game on this day was called off.')).toBeVisible();
    await expect(filters.getByRole('link')).toHaveText(['All 0', 'Seat open 0', 'Called off 0']);
  });

  test('the booking an exception was refused over opens on its day, marked', async ({
    page,
    club,
  }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL' });
    club.raketa.courts = [one];
    const day = dayFromToday(6);
    club.bookings.book(one, day, 17);
    const held = club.bookings.book(one, day, 18);
    await signIn(page);
    await page.goto('/courts');
    const exceptions = page.getByRole('region', { name: 'Exceptions' });
    await exceptions.getByRole('button', { name: '+ Add an exception' }).click();
    await exceptions.getByRole('radio', { name: 'Hours on a day' }).check();
    await exceptions.getByLabel('Day', { exact: true }).fill(day);
    await exceptions.getByLabel('From').selectOption('18:00');
    await exceptions.getByLabel('Until').selectOption('19:00');
    await exceptions.getByLabel('Reason').fill('Repair');
    await exceptions.getByRole('button', { name: 'Add exception' }).click();

    await exceptions.getByRole('link', { name: 'See the booking' }).click();
    await expect(page.getByRole('heading', { name: 'Bookings', level: 1 })).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`date=${day}&booking=${held.booking_id}$`));
    await expect(rowAt(page, '18:00–19:00')).toHaveAttribute('aria-current', 'true');
    await expect(rowAt(page, '18:00–19:00')).toBeInViewport();
    await expect(rowAt(page, '17:00–18:00')).not.toHaveAttribute('aria-current');
  });

  test.describe('a booked game', () => {
    test('Move lists the free courts of its sport at its hour, and moves it there', async ({
      page,
      stub,
      club,
    }) => {
      const hours = week(EVERY_DAY, 7, 23);
      const one = court({ name: 'Court 1', sport: 'PADEL', hours });
      const two = court({ name: 'Court 2', sport: 'PADEL', hours });
      const off = court({ name: 'Court 3', sport: 'PADEL', hours, offered: false });
      const mornings = court({ name: 'Court 4', sport: 'PADEL', hours: week(EVERY_DAY, 7, 12) });
      const held = court({ name: 'Court 5', sport: 'PADEL', hours });
      const tennis = court({ name: 'Kort tenisowy', sport: 'TENNIS', hours });
      club.raketa.courts = [one, two, off, mornings, held, tennis];
      const day = dayFromToday(2);
      const game = club.bookings.add(booking({ court: one, day, hour: 19 }));
      club.bookings.add(booking({ court: held, day, hour: 19 }));
      await openDay(page, day);

      await rowAt(page, '19:00–20:00')
        .filter({ hasText: 'Court 1' })
        .getByRole('button', { name: /^Move/ })
        .click();
      const dialog = page.getByRole('dialog', { name: /^Move the 19:00 game on / });
      await expect(dialog).toContainText(
        'It is on Court 1. The players see the new court; nothing else about the game changes.',
      );
      await expect(dialog.getByRole('radio')).toHaveCount(1);
      await expect(dialog.getByRole('radio', { name: 'Court 2' })).not.toBeChecked();
      await expect(dialog.getByRole('button', { name: 'Move', exact: true })).toBeDisabled();

      await dialog.getByRole('radio', { name: 'Court 2' }).check();
      await dialog.getByRole('button', { name: 'Move', exact: true }).click();

      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^The 19:00 game on .+ is on Court 2 now\. The players see the new court\.$/,
      );
      await expect(page.getByRole('rowheader')).toHaveText([
        /19:00–20:00\s*Court 2/,
        /19:00–20:00\s*Court 5/,
      ]);
      expect(
        stub
          .requests('post', '/api/v1/club/bookings/{booking_id}/move')
          .map((r) => [r.params.booking_id, r.body]),
      ).toEqual([[game.booking_id, { court_id: two.id }]]);
    });

    test('Move with no court free says to cancel instead; a court taken meanwhile says so', async ({
      page,
      stub,
      club,
    }) => {
      const hours = week(EVERY_DAY, 7, 23);
      const one = court({ name: 'Court 1', sport: 'PADEL', hours });
      club.raketa.courts = [one];
      const day = dayFromToday(2);
      club.bookings.add(booking({ court: one, day, hour: 19 }));
      await openDay(page, day);

      await rowAt(page, '19:00–20:00').getByRole('button', { name: /^Move/ }).click();
      const dialog = page.getByRole('dialog', { name: /^Move the 19:00 game on / });
      await expect(dialog).toContainText(
        'No other padel court is free at 19:00. If the court can’t be played, cancel the game with “Repair”.',
      );
      await expect(dialog.getByRole('radio')).toHaveCount(0);
      await dialog.getByRole('button', { name: 'Back' }).click();
      await expect(dialog).toBeHidden();

      const two = court({ name: 'Court 2', sport: 'PADEL', hours });
      club.raketa.courts = [one, two];
      stub.on('post', '/api/v1/club/bookings/{booking_id}/move', () => ({
        status: 409,
        body: refusal('court_just_taken'),
      }));
      await rowAt(page, '19:00–20:00').getByRole('button', { name: /^Move/ }).click();
      await dialog.getByRole('radio', { name: 'Court 2' }).check();
      await dialog.getByRole('button', { name: 'Move', exact: true }).click();
      await expect(page.getByRole('main').getByRole('alert')).toHaveText(
        /^Another game took that court a moment ago\. Move the 19:00 game on .+ again to see the courts still free\.$/,
      );
      await expect(rowAt(page, '19:00–20:00')).toContainText('Court 1');
    });

    test('Cancel before the cut-off asks why, spells out that every hold is let go, and nobody pays', async ({
      page,
      stub,
      club,
    }) => {
      const padel = court({ name: 'Court 1', sport: 'PADEL' });
      club.raketa.courts = [padel];
      const day = dayFromToday(2);
      const game = club.bookings.add(booking({ court: padel, day, hour: 19, stage: 'SEAT_OPEN' }));
      await openDay(page, day);
      const cancellations = () =>
        stub.requests('post', '/api/v1/club/bookings/{booking_id}/cancellation');

      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      const dialog = page.getByRole('dialog', { name: /^Cancel the 19:00 game on .+\?$/ });
      await expect(dialog.getByRole('radiogroup', { name: 'Why' })).toHaveText(
        /^Weather\s*Repair\s*Double booking\s*Other$/,
      );
      await expect(dialog).toContainText(
        'Every hold is let go and nobody pays a fee. It goes on nobody’s record',
      );
      await expect(dialog).not.toContainText('refunded');
      await expect(dialog.getByRole('button', { name: 'Cancel the booking' })).toBeDisabled();
      await dialog.getByRole('button', { name: 'Keep the game' }).click();
      await expect(dialog).toBeHidden();
      expect(cancellations()).toEqual([]);

      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      await expect(dialog.getByRole('radio', { name: 'Weather' })).not.toBeChecked();
      await dialog.getByRole('radio', { name: 'Double booking' }).check();
      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();

      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^You cancelled the 19:00 game on .+\. Every hold is let go: nobody pays\.$/,
      );
      const row = rowAt(page, '19:00–20:00');
      await expect(row.getByRole('cell').nth(2)).toHaveText(
        /Called off\s*Cancelled by you · Double booking/,
      );
      // Nothing was taken, so nothing is refunded, and no share is held any more.
      await expect(row.getByRole('cell').nth(3)).toHaveText(/Collected\s*0 zł\s*Refunded\s*0 zł/);
      await expect(row.getByRole('cell').nth(1).getByRole('listitem')).toHaveText([
        'Anna Nowak',
        'Piotr Sikora',
        'Kasia Wiśniewska',
        'Open seat',
      ]);
      await expect(row.getByRole('button')).toHaveCount(0);
      // The dialog says the game is called off, so it is, even were another court free (#672):
      // previewing a move is the dialog's to come (#675).
      expect(cancellations().map((r) => [r.params.booking_id, r.body])).toEqual([
        [game.booking_id, { reason: 'DOUBLE_BOOKING', anyway: true }],
      ]);
    });

    test('Cancel after the cut-off spells out that everyone is refunded in full, the card fees not returned', async ({
      page,
      club,
    }) => {
      const padel = court({ name: 'Court 1', sport: 'PADEL' });
      club.raketa.courts = [padel];
      const day = dayFromToday(1);
      club.bookings.add(booking({ court: padel, day, hour: 19, cut_off: fromNow(-HOUR_MS) }));
      await openDay(page, day);
      const row = rowAt(page, '19:00–20:00');
      await expect(row.getByRole('cell').nth(3)).toHaveText(/Collected\s*140 zł\s*Refunded\s*0 zł/);

      await row.getByRole('button', { name: /^Cancel/ }).click();
      const dialog = page.getByRole('dialog', { name: /^Cancel the 19:00 game on .+\?$/ });
      await expect(dialog).toContainText(
        'Everyone is refunded in full; the card fees are not returned. It goes on nobody’s record',
      );
      await expect(dialog).not.toContainText('hold');
      await dialog.getByRole('radio', { name: 'Weather' }).check();
      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();

      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^You cancelled the 19:00 game on .+\. Everyone is refunded in full\.$/,
      );
      await expect(row.getByRole('cell').nth(3)).toHaveText(
        /Collected\s*140 zł\s*Refunded\s*140 zł/,
      );
    });

    test('once it has started it is neither moved nor cancelled, and a page read before says why', async ({
      page,
      stub,
      club,
    }) => {
      const padel = court({ name: 'Court 1', sport: 'PADEL' });
      club.raketa.courts = [padel];
      const started = club.bookings.add(booking({ court: padel, day: dayFromToday(0), hour: 7 }));
      started.starts_at = fromNow(-30 * MINUTE_MS);
      const day = clubTime(started.starts_at).day;
      await openDay(page, day);
      await expect(page.getByRole('rowheader')).toHaveCount(1);
      await expect(page.getByRole('row').nth(1).getByRole('button')).toHaveCount(0);

      started.starts_at = fromNow(-2 * 60 * MINUTE_MS);
      await page.reload();
      await expect(page.getByRole('row').nth(1).getByRole('cell').nth(2)).toHaveText('Played');

      // The page was read while the game was still ahead; by the press it had begun.
      const later = dayFromToday(2);
      const game = club.bookings.add(booking({ court: padel, day: later, hour: 19 }));
      await page.goto(`/bookings?date=${later}`);
      stub.on('get', '/api/v1/club/bookings/{booking_id}/free-courts', () => ({
        status: 409,
        body: refusal('game_has_started'),
      }));
      stub.on('post', '/api/v1/club/bookings/{booking_id}/cancellation', () => {
        game.starts_at = fromNow(-MINUTE_MS);
        return { status: 409, body: refusal('game_has_started') };
      });

      await rowAt(page, '19:00–20:00').getByRole('button', { name: /^Move/ }).click();
      const moving = page.getByRole('dialog', { name: /^Move the 19:00 game on / });
      await expect(moving.getByRole('alert')).toHaveText(
        /^The 19:00 game on .+ has started, so it can’t be moved or cancelled any more\.$/,
      );
      await moving.getByRole('button', { name: 'Back' }).click();

      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      const cancelling = page.getByRole('dialog', { name: /^Cancel the 19:00 game on / });
      await cancelling.getByRole('radio', { name: 'Repair' }).check();
      await cancelling.getByRole('button', { name: 'Cancel the booking' }).click();
      await expect(page.getByRole('main').getByRole('alert')).toHaveText(
        /^The 19:00 game on .+ has started, so it can’t be moved or cancelled any more\.$/,
      );
    });
  });
});
