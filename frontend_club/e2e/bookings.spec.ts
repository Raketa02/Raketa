import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { booking } from './stub/bookings';
import { fromNow } from './stub/club';
import { clubTime, dayFromToday } from './stub/clock';
import { court, week } from './stub/courts';

/**
 * **Bookings** (#563, #674, #675, the screens B4, the mechanics §16.7, §16.9 and §16.16): every
 * Rakieta booking at the club, one day at a time, with its court and the court's kind, its
 * players, its status, its money and the group it came from, and the games the club moves or
 * cancels. No club confirms a game (Q121), so nothing on the page waits for the desk's answer. A
 * cancel moves the game when another of the club's courts takes it (Q122), and the dialog says
 * which it will be before the desk confirms.
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
      indoor: false,
      hours: week(EVERY_DAY, 7, 23),
    });
    club.rakieta.courts = [padel, tennis];
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

    // Soonest first, and only that day's, each court with its kind.
    await expect(page.getByRole('rowheader')).toHaveText([
      /^18:00–19:00\s*Kort centralny · outdoor$/,
      /^19:00–20:00\s*Court 1 · indoor$/,
    ]);

    const seatOpen = rowAt(page, '18:00–19:00');
    await expect(seatOpen.getByRole('cell').nth(0)).toHaveText('Tennis · Friendly');
    // Each player by their whole nickname, never with an @ (ADR-0199 §5).
    await expect(seatOpen.getByRole('cell').nth(1).getByRole('listitem')).toHaveText([
      /^ania\.k\s*taken$/,
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
      /^ania\.k\s*held$/,
      /^piotr\.s\s*held$/,
      /^kasia_w\s*held$/,
      /^marek-z\s*held$/,
    ]);
    await expect(booked.getByRole('cell').nth(2)).toHaveText('Booked');
    await expect(booked.getByRole('cell').nth(3)).toHaveText(
      /Price\s*140 zł\s*Collected\s*0 zł\s*Refunded\s*0 zł/,
    );
    await expect(booked.getByRole('cell').nth(4)).toHaveText(/Ogrody 33 Club\s*Official group/);
  });

  test('Bookings is in the top bar, and opens on today', async ({ page, stub, club }) => {
    const padel = court({ name: 'Court 1', sport: 'PADEL' });
    club.rakieta.courts = [padel];
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
    club.rakieta.courts = [padel];
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
    club.rakieta.courts = [padel];
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
    club.bookings.add(
      booking({
        court: padel,
        day,
        hour: 13,
        stage: 'CALLED_OFF',
        called_off_reason: 'BY_THE_SENDER',
      }),
    );
    const nameless = club.bookings.add(
      booking({ court: padel, day, hour: 12, cut_off: fromNow(-HOUR_MS) }),
    );
    nameless.players = nameless.players.map((player, index) =>
      index === 3 ? { ...player, nickname: null } : player,
    );

    await openDay(page, day);

    await expect(page.getByRole('rowheader')).toHaveCount(4);
    await expect(rowAt(page, '10:00–11:00').getByRole('cell').nth(2)).toHaveText(
      /Called off\s*Cancelled by you · Double booking/,
    );
    await expect(rowAt(page, '10:00–11:00').getByRole('cell').nth(4)).toHaveText(
      'A group that’s gone',
    );
    await expect(rowAt(page, '11:00–12:00').getByRole('cell').nth(2)).toHaveText(
      /Called off\s*Short at the cut-off/,
    );
    await expect(rowAt(page, '13:00–14:00').getByRole('cell').nth(2)).toHaveText(
      /Called off\s*Cancelled by the player who booked it/,
    );
    await expect(
      rowAt(page, '12:00–13:00').getByRole('cell').nth(1).getByRole('listitem').last(),
    ).toHaveText(/^A player\s*taken$/);
  });

  test('‹ and › walk the days, the date box opens any, and Today comes back', async ({
    page,
    stub,
    club,
  }) => {
    const padel = court({ name: 'Court 1', sport: 'PADEL' });
    club.rakieta.courts = [padel];
    club.bookings.add(booking({ court: padel, day: dayFromToday(1), hour: 19 }));
    const day = page.getByRole('navigation', { name: 'Day' });
    const lastQuery = () => stub.requests('get', '/api/v1/club/bookings').at(-1)?.query;
    await signIn(page);
    await page.goto('/bookings');

    await expect(day.getByRole('heading', { name: /^Today · / })).toBeVisible();
    await expect(page.getByText('No Rakieta bookings on this day.')).toBeVisible();
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
    club.rakieta.courts = [padel];
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
    club.rakieta.courts = [one];
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
    test('Move lists the free courts of its sport at its hour, of its kind or indoor, each with its kind, and moves it there', async ({
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
      const outside = court({ name: 'Court 6', sport: 'PADEL', indoor: false, hours });
      const tennis = court({ name: 'Kort tenisowy', sport: 'TENNIS', hours });
      club.rakieta.courts = [one, two, off, mornings, held, outside, tennis];
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
        'It is on Court 1 · indoor. The players are told the new court; nothing else about the game changes.',
      );
      // Never outdoors from indoors: Court 6 is free, and a different game to the players.
      await expect(dialog.getByRole('radio')).toHaveCount(1);
      await expect(dialog.getByRole('radio', { name: 'Court 2 · indoor' })).not.toBeChecked();
      await expect(dialog.getByRole('button', { name: 'Move', exact: true })).toBeDisabled();

      await dialog.getByRole('radio', { name: 'Court 2 · indoor' }).check();
      await dialog.getByRole('button', { name: 'Move', exact: true }).click();

      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^The 19:00 game on .+ is on Court 2 · indoor now, and the players are told\.$/,
      );
      await expect(page.getByRole('rowheader')).toHaveText([
        /19:00–20:00\s*Court 2 · indoor/,
        /19:00–20:00\s*Court 5 · indoor/,
      ]);
      expect(
        stub
          .requests('post', '/api/v1/club/bookings/{booking_id}/move')
          .map((r) => [r.params.booking_id, r.body]),
      ).toEqual([[game.booking_id, { court_id: two.id }]]);
    });

    test('Move offers an outdoor game an outdoor court or an indoor one, as served', async ({
      page,
      club,
    }) => {
      const hours = week(EVERY_DAY, 7, 23);
      const one = court({ name: 'Court 1', sport: 'PADEL', indoor: false, hours });
      const two = court({ name: 'Court 2', sport: 'PADEL', hours });
      const three = court({ name: 'Court 3', sport: 'PADEL', indoor: false, hours });
      club.rakieta.courts = [one, two, three];
      const day = dayFromToday(2);
      club.bookings.add(booking({ court: one, day, hour: 19 }));
      await openDay(page, day);
      await expect(page.getByRole('rowheader')).toHaveText([/19:00–20:00\s*Court 1 · outdoor/]);

      await rowAt(page, '19:00–20:00').getByRole('button', { name: /^Move/ }).click();
      const dialog = page.getByRole('dialog', { name: /^Move the 19:00 game on / });
      await expect(dialog).toContainText('It is on Court 1 · outdoor.');
      await expect(dialog.getByRole('radio')).toHaveCount(2);
      await expect(dialog.getByRole('radiogroup', { name: 'Move it to' })).toHaveText(
        /^Court 2 · indoor\s*Court 3 · outdoor$/,
      );

      await dialog.getByRole('radio', { name: 'Court 2 · indoor' }).check();
      await dialog.getByRole('button', { name: 'Move', exact: true }).click();
      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^The 19:00 game on .+ is on Court 2 · indoor now, and the players are told\.$/,
      );
      await expect(page.getByRole('rowheader')).toHaveText([/19:00–20:00\s*Court 2 · indoor/]);
    });

    test('Move with no indoor court free for an indoor game says to cancel instead; a court taken meanwhile says so', async ({
      page,
      stub,
      club,
    }) => {
      const hours = week(EVERY_DAY, 7, 23);
      const one = court({ name: 'Court 1', sport: 'PADEL', hours });
      const outside = court({ name: 'Court 6', sport: 'PADEL', indoor: false, hours });
      club.rakieta.courts = [one, outside];
      const day = dayFromToday(2);
      club.bookings.add(booking({ court: one, day, hour: 19 }));
      await openDay(page, day);

      await rowAt(page, '19:00–20:00').getByRole('button', { name: /^Move/ }).click();
      const dialog = page.getByRole('dialog', { name: /^Move the 19:00 game on / });
      await expect(dialog).toContainText(
        'No other indoor padel court is free at 19:00. If the court can’t be played, cancel the game with “Repair”.',
      );
      await expect(dialog.getByRole('radio')).toHaveCount(0);
      await dialog.getByRole('button', { name: 'Back' }).click();
      await expect(dialog).toBeHidden();

      const two = court({ name: 'Court 2', sport: 'PADEL', hours });
      club.rakieta.courts = [one, two, outside];
      stub.on('post', '/api/v1/club/bookings/{booking_id}/move', () => ({
        status: 409,
        body: refusal('court_just_taken'),
      }));
      await rowAt(page, '19:00–20:00').getByRole('button', { name: /^Move/ }).click();
      await dialog.getByRole('radio', { name: 'Court 2 · indoor' }).check();
      await dialog.getByRole('button', { name: 'Move', exact: true }).click();
      await expect(page.getByRole('main').getByRole('alert')).toHaveText(
        /^Another game took that court a moment ago\. Move the 19:00 game on .+ again to see the courts still free\.$/,
      );
      await expect(rowAt(page, '19:00–20:00')).toContainText('Court 1 · indoor');
    });

    test('Cancel asks why, then says the game moves to another court of its kind, and the cancel moves it there: nobody is refunded', async ({
      page,
      stub,
      club,
    }) => {
      const hours = week(EVERY_DAY, 7, 23);
      const two = court({ name: 'Court 2', sport: 'PADEL', hours });
      const three = court({ name: 'Court 3', sport: 'PADEL', hours });
      const outside = court({ name: 'Court 4', sport: 'PADEL', indoor: false, hours });
      club.rakieta.courts = [two, three, outside];
      const day = dayFromToday(2);
      const game = club.bookings.add(booking({ court: two, day, hour: 19 }));
      await openDay(page, day);
      const previews = () =>
        stub.requests('get', '/api/v1/club/bookings/{booking_id}/cancellation/preview');

      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      const dialog = page.getByRole('dialog', { name: /^Cancel the 19:00 game on .+\?$/ });
      // The reason first: what a cancel does depends on it.
      await expect(dialog.getByRole('radiogroup', { name: 'Why' })).toHaveText(
        /^Weather\s*Repair\s*Double booking\s*Other$/,
      );
      await expect(dialog).not.toContainText('This game');
      await expect(dialog.getByRole('button', { name: 'Cancel the booking' })).toBeDisabled();
      await expect(dialog.getByRole('button', { name: 'Cancel the game anyway' })).toHaveCount(0);
      expect(previews()).toEqual([]);

      await dialog.getByRole('radio', { name: 'Repair' }).check();
      await expect(dialog.getByRole('status')).toHaveText(
        /^This game moves to Court 3 · indoor · the players are told, nobody is refunded\./,
      );
      await expect(dialog.getByRole('status')).toContainText(
        '“Cancel the game anyway” calls it off instead, for an hour you’re closing whole: every hold is let go and nobody pays a fee.',
      );
      await expect(dialog.getByRole('button', { name: 'Cancel the booking' })).toBeEnabled();
      await expect(dialog.getByRole('button', { name: 'Cancel the game anyway' })).toBeEnabled();
      expect(previews().map((r) => [r.params.booking_id, r.query])).toEqual([
        [game.booking_id, { reason: 'REPAIR' }],
      ]);

      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();

      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^The 19:00 game on .+ moved to Court 3 · indoor: the players are told, and nobody is refunded\.$/,
      );
      // The game goes on, on Court 3: every share still held, and Move and Cancel still the club's.
      const row = rowAt(page, '19:00–20:00');
      await expect(page.getByRole('rowheader')).toHaveText([/19:00–20:00\s*Court 3 · indoor/]);
      await expect(row.getByRole('cell').nth(2)).toHaveText('Booked');
      await expect(row.getByRole('cell').nth(1).getByRole('listitem')).toHaveText([
        /held$/,
        /held$/,
        /held$/,
        /held$/,
      ]);
      await expect(row.getByRole('cell').nth(3)).toHaveText(/Collected\s*0 zł\s*Refunded\s*0 zł/);
      await expect(row.getByRole('button')).toHaveText(['Move', 'Cancel']);
      expect(
        stub
          .requests('post', '/api/v1/club/bookings/{booking_id}/cancellation')
          .map((r) => [r.params.booking_id, r.body]),
      ).toEqual([[game.booking_id, { reason: 'REPAIR', anyway: false }]]);
    });

    test('a weather cancel moves an outdoor game indoors only, and the dialog reads again as the reason changes', async ({
      page,
      stub,
      club,
    }) => {
      const hours = week(EVERY_DAY, 7, 23);
      const one = court({ name: 'Court 1', sport: 'PADEL', indoor: false, hours });
      const two = court({ name: 'Court 2', sport: 'PADEL', indoor: false, hours });
      const three = court({ name: 'Court 3', sport: 'PADEL', hours });
      club.rakieta.courts = [one, two, three];
      const day = dayFromToday(2);
      club.bookings.add(booking({ court: one, day, hour: 19 }));
      await openDay(page, day);

      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      const dialog = page.getByRole('dialog', { name: /^Cancel the 19:00 game on .+\?$/ });
      // The same kind first…
      await dialog.getByRole('radio', { name: 'Repair' }).check();
      await expect(dialog.getByRole('status')).toContainText(
        'This game moves to Court 2 · outdoor · the players are told, nobody is refunded.',
      );
      // …but an outdoor court at the same hour is rained on too.
      await dialog.getByRole('radio', { name: 'Weather' }).check();
      await expect(dialog.getByRole('status')).toContainText(
        'This game moves to Court 3 · indoor · the players are told, nobody is refunded.',
      );
      expect(
        stub
          .requests('get', '/api/v1/club/bookings/{booking_id}/cancellation/preview')
          .map((r) => r.query.reason),
      ).toEqual(['REPAIR', 'WEATHER']);

      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();
      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^The 19:00 game on .+ moved to Court 3 · indoor: the players are told, and nobody is refunded\.$/,
      );
      await expect(page.getByRole('rowheader')).toHaveText([/19:00–20:00\s*Court 3 · indoor/]);
    });

    test('Cancel before the cut-off, with only an outdoor court free for an indoor game, says the game is called off: every hold let go, and nobody pays', async ({
      page,
      stub,
      club,
    }) => {
      const hours = week(EVERY_DAY, 7, 23);
      const padel = court({ name: 'Court 1', sport: 'PADEL', hours });
      // Free, but outdoors: never for an indoor game.
      const outside = court({ name: 'Court 6', sport: 'PADEL', indoor: false, hours });
      club.rakieta.courts = [padel, outside];
      const day = dayFromToday(2);
      const game = club.bookings.add(booking({ court: padel, day, hour: 19, stage: 'SEAT_OPEN' }));
      await openDay(page, day);
      const cancellations = () =>
        stub.requests('post', '/api/v1/club/bookings/{booking_id}/cancellation');

      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      const dialog = page.getByRole('dialog', { name: /^Cancel the 19:00 game on .+\?$/ });
      await dialog.getByRole('radio', { name: 'Repair' }).check();
      await expect(dialog.getByRole('status')).toHaveText(
        'This game is called off: every hold is let go and nobody pays a fee. It goes on nobody’s ' +
          'record, the players are offered another game first, and the hour is yours to sell again.',
      );
      await expect(dialog).not.toContainText('refunded');
      await expect(dialog.getByRole('button', { name: 'Cancel the game anyway' })).toHaveCount(0);
      await dialog.getByRole('button', { name: 'Keep the game' }).click();
      await expect(dialog).toBeHidden();
      expect(cancellations()).toEqual([]);

      // Asked again, the reason starts unchosen, and nothing is said until it is.
      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      await expect(dialog.getByRole('radio', { name: 'Repair' })).not.toBeChecked();
      await expect(dialog).not.toContainText('This game');
      await dialog.getByRole('radio', { name: 'Double booking' }).check();
      await expect(dialog.getByRole('status')).toContainText('This game is called off');
      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();

      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^The 19:00 game on .+ is called off\. Every hold is let go: nobody pays\.$/,
      );
      const row = rowAt(page, '19:00–20:00');
      await expect(row.getByRole('cell').nth(2)).toHaveText(
        /Called off\s*Cancelled by you · Double booking/,
      );
      // Nothing was taken, so nothing is refunded, and no share is held any more.
      await expect(row.getByRole('cell').nth(3)).toHaveText(/Collected\s*0 zł\s*Refunded\s*0 zł/);
      await expect(row.getByRole('cell').nth(1).getByRole('listitem')).toHaveText([
        'ania.k',
        'piotr.s',
        'kasia_w',
        'Open seat',
      ]);
      await expect(row.getByRole('button')).toHaveCount(0);
      expect(cancellations().map((r) => [r.params.booking_id, r.body])).toEqual([
        [game.booking_id, { reason: 'DOUBLE_BOOKING', anyway: false }],
      ]);
    });

    test('Cancel after the cut-off says everyone is refunded in full, the card fees not returned', async ({
      page,
      club,
    }) => {
      const padel = court({ name: 'Court 1', sport: 'PADEL' });
      club.rakieta.courts = [padel];
      const day = dayFromToday(1);
      club.bookings.add(booking({ court: padel, day, hour: 19, cut_off: fromNow(-HOUR_MS) }));
      await openDay(page, day);
      const row = rowAt(page, '19:00–20:00');
      await expect(row.getByRole('cell').nth(3)).toHaveText(/Collected\s*140 zł\s*Refunded\s*0 zł/);

      await row.getByRole('button', { name: /^Cancel/ }).click();
      const dialog = page.getByRole('dialog', { name: /^Cancel the 19:00 game on .+\?$/ });
      await dialog.getByRole('radio', { name: 'Weather' }).check();
      await expect(dialog.getByRole('status')).toHaveText(
        /^This game is called off: everyone is refunded in full; the card fees are not returned\. It goes on nobody’s record/,
      );
      await expect(dialog).not.toContainText('hold');
      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();

      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^The 19:00 game on .+ is called off\. Everyone is refunded in full\.$/,
      );
      await expect(row.getByRole('cell').nth(3)).toHaveText(
        /Collected\s*140 zł\s*Refunded\s*140 zł/,
      );
    });

    test('Cancel the game anyway calls it off though another court would take it', async ({
      page,
      stub,
      club,
    }) => {
      const hours = week(EVERY_DAY, 7, 23);
      const one = court({ name: 'Court 1', sport: 'PADEL', hours });
      const two = court({ name: 'Court 2', sport: 'PADEL', hours });
      club.rakieta.courts = [one, two];
      const day = dayFromToday(1);
      const game = club.bookings.add(
        booking({ court: one, day, hour: 19, cut_off: fromNow(-HOUR_MS) }),
      );
      await openDay(page, day);

      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      const dialog = page.getByRole('dialog', { name: /^Cancel the 19:00 game on .+\?$/ });
      await dialog.getByRole('radio', { name: 'Other' }).check();
      await expect(dialog.getByRole('status')).toHaveText(
        'This game moves to Court 2 · indoor · the players are told, nobody is refunded. ' +
          '“Cancel the game anyway” calls it off instead, for an hour you’re closing whole: ' +
          'everyone is refunded in full; the card fees are not returned.',
      );
      await dialog.getByRole('button', { name: 'Cancel the game anyway' }).click();

      await expect(page.getByRole('main').getByRole('status')).toHaveText(
        /^The 19:00 game on .+ is called off\. Everyone is refunded in full\.$/,
      );
      const row = rowAt(page, '19:00–20:00');
      await expect(page.getByRole('rowheader')).toHaveText([/19:00–20:00\s*Court 1 · indoor/]);
      await expect(row.getByRole('cell').nth(2)).toHaveText(
        /Called off\s*Cancelled by you · Other/,
      );
      await expect(row.getByRole('cell').nth(3)).toHaveText(
        /Collected\s*140 zł\s*Refunded\s*140 zł/,
      );
      expect(
        stub
          .requests('post', '/api/v1/club/bookings/{booking_id}/cancellation')
          .map((r) => [r.params.booking_id, r.body]),
      ).toEqual([[game.booking_id, { reason: 'OTHER', anyway: true }]]);
    });

    test('the cancel decides afresh: its answer says where the game went, or that it is off, when that is not what the dialog said', async ({
      page,
      stub,
      club,
    }) => {
      const hours = week(EVERY_DAY, 7, 23);
      const one = court({ name: 'Court 1', sport: 'PADEL', hours });
      const three = court({ name: 'Court 3', sport: 'PADEL', hours });
      const four = court({ name: 'Court 4', sport: 'PADEL', hours });
      club.rakieta.courts = [one, three, four];
      const day = dayFromToday(2);
      club.bookings.add(booking({ court: one, day, hour: 18 }));
      club.bookings.add(booking({ court: one, day, hour: 19 }));
      club.bookings.add(booking({ court: one, day, hour: 20 }));
      await openDay(page, day);
      const dialog = page.getByRole('dialog', { name: /^Cancel the \d\d:00 game on .+\?$/ });
      const notice = page.getByRole('main').getByRole('status');

      // Court 3, said; taken before the confirm: Court 4 takes the game instead.
      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      await dialog.getByRole('radio', { name: 'Repair' }).check();
      await expect(dialog.getByRole('status')).toContainText('This game moves to Court 3 · indoor');
      club.bookings.add(booking({ court: three, day, hour: 19 }));
      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();
      await expect(notice).toHaveText(
        /^Court 3 was taken a moment ago, so the 19:00 game on .+ moved to Court 4 · indoor: the players are told, and nobody is refunded\.$/,
      );
      await expect(rowAt(page, '19:00–20:00').getByRole('rowheader')).toHaveText([
        /Court 4 · indoor/,
        /Court 3 · indoor/,
      ]);

      // Court 3, said; every court taken before the confirm: the game is off.
      await rowAt(page, '18:00–19:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      await dialog.getByRole('radio', { name: 'Repair' }).check();
      await expect(dialog.getByRole('status')).toContainText('This game moves to Court 3 · indoor');
      club.bookings.add(booking({ court: three, day, hour: 18 }));
      club.bookings.add(booking({ court: four, day, hour: 18 }));
      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();
      await expect(notice).toHaveText(
        /^Court 3 was taken a moment ago, so the 18:00 game on .+ is called off\. Every hold is let go: nobody pays\.$/,
      );

      // Called off, said; a court came free before the confirm: the game moves there.
      club.bookings.add(booking({ court: three, day, hour: 20 }));
      club.bookings.add(booking({ court: four, day, hour: 20 }));
      await rowAt(page, '20:00–21:00')
        .filter({ hasText: 'Court 1' })
        .getByRole('button', { name: /^Cancel/ })
        .click();
      await dialog.getByRole('radio', { name: 'Repair' }).check();
      await expect(dialog.getByRole('status')).toContainText('This game is called off');
      club.rakieta.courts = [one, three, four, court({ name: 'Court 5', sport: 'PADEL', hours })];
      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();
      await expect(notice).toHaveText(
        /^A court came free a moment ago, so the 20:00 game on .+ moved to Court 5 · indoor: the players are told, and nobody is refunded\.$/,
      );

      // The court it would move to went to another game as the cancel landed: nothing happened.
      stub.on('post', '/api/v1/club/bookings/{booking_id}/cancellation', () => ({
        status: 409,
        body: refusal('court_just_taken'),
      }));
      await rowAt(page, '20:00–21:00')
        .filter({ hasText: 'Court 5' })
        .getByRole('button', { name: /^Cancel/ })
        .click();
      await dialog.getByRole('radio', { name: 'Other' }).check();
      await expect(dialog.getByRole('status')).toContainText('This game');
      await dialog.getByRole('button', { name: 'Cancel the booking' }).click();
      await expect(page.getByRole('main').getByRole('alert')).toHaveText(
        /^The court that would have taken the 20:00 game on .+ went to another game a moment ago\. Cancel it again to see what a cancel does now\.$/,
      );
    });

    test('once it has started it is neither moved nor cancelled, and a page read before says why', async ({
      page,
      stub,
      club,
    }) => {
      const padel = court({ name: 'Court 1', sport: 'PADEL' });
      club.rakieta.courts = [padel];
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

      await rowAt(page, '19:00–20:00').getByRole('button', { name: /^Move/ }).click();
      const moving = page.getByRole('dialog', { name: /^Move the 19:00 game on / });
      await expect(moving.getByRole('alert')).toHaveText(
        /^The 19:00 game on .+ has started, so it can’t be moved or cancelled any more\.$/,
      );
      await moving.getByRole('button', { name: 'Back' }).click();

      // Asked what a cancel would do, the backend says it has begun: nothing to confirm.
      stub.on('get', '/api/v1/club/bookings/{booking_id}/cancellation/preview', () => ({
        status: 409,
        body: refusal('game_has_started'),
      }));
      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      const cancelling = page.getByRole('dialog', { name: /^Cancel the 19:00 game on / });
      await cancelling.getByRole('radio', { name: 'Repair' }).check();
      await expect(cancelling.getByRole('alert')).toHaveText(
        /^The 19:00 game on .+ has started, so it can’t be moved or cancelled any more\.$/,
      );
      await expect(cancelling.getByRole('button', { name: 'Cancel the booking' })).toBeDisabled();
      await cancelling.getByRole('button', { name: 'Keep the game' }).click();

      // Read again, and begun by the confirm.
      club.bookings.install();
      stub.on('post', '/api/v1/club/bookings/{booking_id}/cancellation', () => {
        game.starts_at = fromNow(-MINUTE_MS);
        return { status: 409, body: refusal('game_has_started') };
      });
      await rowAt(page, '19:00–20:00')
        .getByRole('button', { name: /^Cancel/ })
        .click();
      await cancelling.getByRole('radio', { name: 'Repair' }).check();
      await expect(cancelling.getByRole('status')).toContainText('This game is called off');
      await cancelling.getByRole('button', { name: 'Cancel the booking' }).click();
      await expect(page.getByRole('main').getByRole('alert')).toHaveText(
        /^The 19:00 game on .+ has started, so it can’t be moved or cancelled any more\.$/,
      );
    });
  });
});
