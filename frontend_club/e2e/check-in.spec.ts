import type { Page } from '@playwright/test';

import { fakeCamera } from './camera';
import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { booking } from './stub/bookings';
import type { FakeClub } from './stub/club';
import { atClubHour, dayFromToday } from './stub/clock';
import { court } from './stub/courts';

/**
 * **Check in** (#564, the screens B6, the mechanics §15.1 and §16.10): a club that checks players
 * in scans a player's QR code with the device's camera, or types the short code under it, and
 * sees the game and the player checked in, or why not.
 */

const CHECK_IN = '/bookings/check-in';
const ANSWERS = '/api/v1/club/check-ins';

/** A club that checks players in, with one padel court, Court 2. */
function checkingIn(club: FakeClub) {
  club.raketa.settings.check_in = true;
  const padel = court({ name: 'Court 2', sport: 'PADEL' });
  club.raketa.courts = [padel];
  return padel;
}

async function openCheckIn(page: Page) {
  await signIn(page);
  await page.goto(CHECK_IN);
  await expect(page.getByRole('heading', { name: 'Check in', level: 1 })).toBeVisible();
}

function shortCode(page: Page) {
  return page.getByLabel('Short code', { exact: true });
}

/** Why the last code checked nobody in, as the page says it. */
function refused(page: Page) {
  return page.getByRole('main').getByRole('alert');
}

async function typeCode(page: Page, code: string) {
  await shortCode(page).fill(code);
  await page.getByRole('button', { name: 'Check in', exact: true }).click();
}

/** *Sat 3 Oct*, as the page names a local day. */
function shortDay(day: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'UTC',
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  })
    .format(new Date(`${day}T12:00:00Z`))
    .replace(',', '');
}

test.describe('Check in', () => {
  test('Bookings offers Check in only to a club that checks players in', async ({
    page,
    stub,
    club,
  }) => {
    await fakeCamera(page);
    await signIn(page);
    await page.goto('/bookings');
    await expect(page.getByRole('heading', { name: 'Bookings', level: 1 })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Check in' })).toHaveCount(0);

    club.raketa.settings.check_in = true;
    // Settings that could not be read leave the button off, never the day.
    const settings = stub.requests('get', '/api/v1/club/raketa-settings').length;
    stub.on('get', '/api/v1/club/raketa-settings', () => ({
      status: 500,
      body: refusal('internal_error'),
    }));
    await page.reload();
    await expect(page.getByRole('heading', { name: /^Today · / })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Check in' })).toHaveCount(0);
    expect(stub.requests('get', '/api/v1/club/raketa-settings').length).toBeGreaterThan(settings);

    // The fake's own settings again, which say the club checks players in.
    club.raketa.install();
    await page.reload();
    await page.getByRole('link', { name: 'Check in' }).click();

    await expect(page).toHaveURL(/\/bookings\/check-in$/);
    await expect(page.getByRole('heading', { name: 'Check in', level: 1 })).toBeVisible();
    await expect(
      page
        .getByRole('navigation', { name: 'Club website' })
        .getByRole('link', { name: 'Bookings' }),
    ).toHaveAttribute('aria-current', 'page');
  });

  test('a short code typed by hand checks the player in, and Bookings shows it', async ({
    page,
    stub,
    club,
  }) => {
    const padel = checkingIn(club);
    const game = club.bookings.add(booking({ court: padel, day: dayFromToday(0), hour: 19 }));
    const { short } = club.bookings.checkInCode(game, 1);
    await fakeCamera(page);
    await openCheckIn(page);

    // However the desk spaced or cased it.
    await typeCode(page, ` ${short.slice(0, 3).toLowerCase()} ${short.slice(3).toLowerCase()} `);

    await expect(page.getByText('19:00 · Court 2 · Padel')).toBeVisible();
    await expect(page.getByText('Piotr Sikora — checked in ✓')).toBeVisible();
    // The box is ready for the next player.
    await expect(shortCode(page)).toHaveValue('');
    expect(stub.requests('post', ANSWERS).map((each) => each.body)).toEqual([{ code: short }]);

    await page
      .getByRole('navigation', { name: 'Club website' })
      .getByRole('link', { name: 'Bookings' })
      .click();
    await expect(page.getByRole('heading', { name: 'Bookings', level: 1 })).toBeVisible();
    await expect(page.getByRole('listitem').filter({ hasText: 'Piotr Sikora' })).toHaveText(
      /Piotr Sikora\s*paid ✓\s*checked in ✓/,
    );
    await expect(page.getByRole('listitem').filter({ hasText: 'Anna Nowak' })).toHaveText(
      /Anna Nowak\s*paid ✓$/,
    );
  });

  test('the camera reads a player’s QR code, asks once while it is held up, then reads the next', async ({
    page,
    stub,
    club,
  }) => {
    const padel = checkingIn(club);
    const game = club.bookings.add(booking({ court: padel, day: dayFromToday(0), hour: 19 }));
    const anna = club.bookings.checkInCode(game, 0);
    const piotr = club.bookings.checkInCode(game, 1);
    const camera = await fakeCamera(page);
    await openCheckIn(page);

    await camera.show(anna.payload);
    await expect(page.getByText('19:00 · Court 2 · Padel')).toBeVisible();
    await expect(page.getByText('Anna Nowak — checked in ✓')).toBeVisible();

    // Anna's phone stays in front of the camera, and the page keeps reading it.
    await camera.lookedAtMore(5);
    await camera.show(piotr.payload);
    await expect(page.getByText('Piotr Sikora — checked in ✓')).toBeVisible();

    // Taken away and held up again, Piotr's code is asked about again.
    await camera.clear();
    await camera.lookedAtMore(6);
    await camera.show(piotr.payload);
    await expect(refused(page)).toHaveText(/^Already scanned: checked in at \d{2}:\d{2}\.$/);

    expect(stub.requests('post', ANSWERS).map((each) => each.body)).toEqual([
      { code: anna.payload },
      { code: piotr.payload },
      { code: piotr.payload },
    ]);
  });

  test('a code that checks nobody in says why', async ({ page, stub, club }) => {
    const padel = checkingIn(club);
    const today = dayFromToday(0);
    const later = dayFromToday(2);
    const nextWeek = club.bookings.add(booking({ court: padel, day: later, hour: 19 }));
    // Further ahead than a desk looks for a typed code.
    const farAhead = club.bookings.add(booking({ court: padel, day: dayFromToday(20), hour: 19 }));
    const scanned = club.bookings.add(booking({ court: padel, day: today, hour: 18 }));
    scanned.players = scanned.players.map((player, index) =>
      index === 0 ? { ...player, checked_in_at: atClubHour(today, 17, 52) } : player,
    );
    const off = club.bookings.add(
      booking({
        court: padel,
        day: today,
        hour: 20,
        stage: 'CALLED_OFF',
        called_off_reason: 'CANCELLED_BY_THE_CLUB',
        cancel_reason: 'REPAIR',
      }),
    );
    await fakeCamera(page);
    await openCheckIn(page);

    const refusals: [string, string][] = [
      [
        club.bookings.checkInCode(nextWeek, 0).short,
        `This code is for another day: the game is on ${shortDay(later)} at 19:00.`,
      ],
      [club.bookings.checkInCode(scanned, 0).short, 'Already scanned: checked in at 17:52.'],
      [
        club.bookings.checkInCode(off, 0).short,
        'This game is called off, so there’s nobody to check in.',
      ],
      ['ZZZ ZZZ', 'No seat on a booked game has this code. Check it against the player’s phone.'],
      [
        club.bookings.checkInCode(farAhead, 0).short,
        'No seat on a booked game has this code. Check it against the player’s phone.',
      ],
    ];
    for (const [code, sentence] of refusals) {
      await typeCode(page, code);
      await expect(refused(page)).toHaveText(sentence);
      // A refused code stays in the box, to be corrected.
      await expect(shortCode(page)).toHaveValue(code);
    }

    stub.on('post', ANSWERS, () => ({
      status: 409,
      body: refusal('check_in_code_for_another_club'),
    }));
    await typeCode(page, 'K7M2QX');
    await expect(refused(page)).toHaveText('This code is for a game at another club.');
  });

  test('a scanned code is refused the same way, and a QR code that isn’t Raketa’s is never sent', async ({
    page,
    stub,
    club,
  }) => {
    const padel = checkingIn(club);
    const later = dayFromToday(3);
    const game = club.bookings.add(booking({ court: padel, day: later, hour: 9 }));
    const camera = await fakeCamera(page);
    await openCheckIn(page);

    await camera.show('https://ogrody33.pl/menu');
    await expect(refused(page)).toHaveText('That QR code isn’t a Raketa check-in code.');
    expect(stub.requests('post', ANSWERS)).toHaveLength(0);

    await camera.show(club.bookings.checkInCode(game, 0).payload);
    await expect(refused(page)).toHaveText(
      `This code is for another day: the game is on ${shortDay(later)} at 09:00.`,
    );
  });

  test('a code the page can tell is wrong never reaches the backend', async ({
    page,
    stub,
    club,
  }) => {
    checkingIn(club);
    await fakeCamera(page);
    await openCheckIn(page);

    await typeCode(page, '  ');
    await expect(
      page.getByText('Type the six characters under the player’s QR code.'),
    ).toBeVisible();

    await typeCode(page, 'K7M-2Q');
    await expect(page.getByText('A short code is six characters.')).toBeVisible();
    await expect(shortCode(page)).toHaveAttribute('aria-invalid', 'true');

    // The refusal goes as soon as the box changes.
    await shortCode(page).fill('K7M-2QX');
    await expect(page.getByText('A short code is six characters.')).toHaveCount(0);
    expect(stub.requests('post', ANSWERS)).toHaveLength(0);
  });

  test('a scan the server could not answer can be tried again', async ({ page, stub, club }) => {
    const padel = checkingIn(club);
    const game = club.bookings.add(booking({ court: padel, day: dayFromToday(0), hour: 19 }));
    const { payload } = club.bookings.checkInCode(game, 2);
    let calls = 0;
    stub.on('post', ANSWERS, () => {
      calls += 1;
      if (calls === 1) return { status: 'drop' };
      return {
        status: 200,
        body: {
          booking_id: game.booking_id,
          starts_at: game.starts_at,
          ends_at: atClubHour(dayFromToday(0), 20),
          court_name: 'Court 2',
          sport: 'PADEL',
          kind: 'COMPETITIVE',
          player: { player_id: game.players[2]?.player_id ?? '', name: null },
          checked_in_at: new Date().toISOString(),
        },
      } as const;
    });
    const camera = await fakeCamera(page);
    await openCheckIn(page);

    await camera.show(payload);
    await expect(refused(page)).toHaveText(
      /We couldn't reach the server\. Try again in a moment\./,
    );
    await page.getByRole('button', { name: 'Try again' }).click();

    // A player whose account can no longer be named is still checked in.
    await expect(page.getByText('A player — checked in ✓')).toBeVisible();
    expect(stub.requests('post', ANSWERS).map((each) => each.body)).toEqual([
      { code: payload },
      { code: payload },
    ]);
  });

  test('a camera the browser will not open says why, and the code still works', async ({
    page,
    club,
  }) => {
    const padel = checkingIn(club);
    const game = club.bookings.add(booking({ court: padel, day: dayFromToday(0), hour: 19 }));
    const camera = await fakeCamera(page, { refusal: 'NotAllowedError' });
    await openCheckIn(page);

    await expect(
      page.getByText(
        'The camera is blocked for this site. Allow it in the browser’s settings and try again, ' +
          'or type the short code below.',
      ),
    ).toBeVisible();
    await expect(page.getByText('Hold the player’s QR code up to the camera.')).toHaveCount(0);

    await typeCode(page, club.bookings.checkInCode(game, 3).short);
    await expect(page.getByText('Marek Zając — checked in ✓')).toBeVisible();

    // Allowed in the browser's settings, the camera opens when asked again.
    await camera.allow();
    await page.getByRole('button', { name: 'Try the camera again' }).click();
    await expect(page.getByText('Hold the player’s QR code up to the camera.')).toBeVisible();
    await camera.show(club.bookings.checkInCode(game, 0).payload);
    await expect(page.getByText('Anna Nowak — checked in ✓')).toBeVisible();
  });

  test('a device with no camera says so', async ({ page, club }) => {
    checkingIn(club);
    await fakeCamera(page, { refusal: 'NotFoundError' });
    await openCheckIn(page);

    await expect(
      page.getByText('This device has no camera to use. Type the short code below instead.'),
    ).toBeVisible();
    await expect(shortCode(page)).toBeVisible();
  });

  test('a camera that stops says so, and opens again when asked', async ({ page, club }) => {
    const padel = checkingIn(club);
    const game = club.bookings.add(booking({ court: padel, day: dayFromToday(0), hour: 19 }));
    const camera = await fakeCamera(page);
    await openCheckIn(page);
    await expect(page.getByText('Hold the player’s QR code up to the camera.')).toBeVisible();

    await camera.unplug();
    await expect(
      page.getByText('The camera stopped. Try again, or type the short code below.'),
    ).toBeVisible();

    await page.getByRole('button', { name: 'Try the camera again' }).click();
    await expect(page.getByText('Hold the player’s QR code up to the camera.')).toBeVisible();
    await camera.show(club.bookings.checkInCode(game, 1).payload);
    await expect(page.getByText('Piotr Sikora — checked in ✓')).toBeVisible();
  });

  test('a club that doesn’t check players in is told how to switch it on', async ({
    page,
    stub,
    club,
  }) => {
    await fakeCamera(page);
    await openCheckIn(page);

    await expect(page.getByText('You don’t check players in')).toBeVisible();
    await page.getByRole('link', { name: 'Open Raketa settings' }).click();
    await expect(page.getByRole('heading', { name: 'Raketa settings', level: 1 })).toBeVisible();

    // Switched off while the page was open: the backend refuses, and the page is drawn again.
    club.raketa.settings.check_in = true;
    await page.goto(CHECK_IN);
    await expect(shortCode(page)).toBeVisible();
    club.raketa.settings.check_in = false;
    await typeCode(page, 'K7M2QX');
    await expect(page.getByText('You don’t check players in')).toBeVisible();
    await expect(shortCode(page)).toHaveCount(0);
    expect(stub.requests('post', ANSWERS)).toHaveLength(1);
  });
});
