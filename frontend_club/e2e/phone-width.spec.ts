import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { booking } from './stub/bookings';
import { administrator, DAY_MS, fromNow, joinRequest, officialGroup } from './stub/club';
import { dayFromToday } from './stub/clock';
import { court, week } from './stub/courts';
import { moneyRow, payout } from './stub/money';

/** **Every page works at phone width** (#500 story 95): nothing scrolls sideways at 360 px. */

test.use({ viewport: { width: 360, height: 780 } });

/**
 * **The longest nickname there is**: 64 characters, with no space or hyphen for a line to break at
 * (ADR-0199). A name had spaces; a handle may have none, so only the page's `overflow-wrap` keeps
 * it on a phone.
 */
const LONGEST_NICKNAME = 'malgorzata.szczepanska_wisniewska.ogrody33_wieczorne.granie.krkw';

async function fitsSideways(page: import('@playwright/test').Page, path: string) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, `${path} scrolls sideways by ${overflow}px`).toBeLessThanOrEqual(0);
}

test('the signed-out pages fit a phone', async ({ page }) => {
  for (const path of [
    '/sign-in',
    '/sign-up',
    '/forgot-password',
    '/forgot-password/code',
    '/reset/a-link',
  ]) {
    await page.goto(path);
    await expect(page.getByText('Raketa for Clubs').first()).toBeVisible();
    await fitsSideways(page, path);
  }
});

test('the signed-in pages fit a phone, top bar and all', async ({ page, club }) => {
  // The fake club answers the sign-in: without it, this test leaned on the one before it.
  void club;
  await signIn(page);
  for (const path of [
    '/overview',
    '/bookings',
    '/courts',
    '/money',
    '/groups',
    '/administrators',
    '/details',
    '/rakieta-settings',
  ]) {
    await page.goto(path);
    await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Club website' })).toBeVisible();
    await fitsSideways(page, path);
  }
});

test('Administrators fits a phone: its rows, its form, its banner and its question', async ({
  page,
  club,
}) => {
  club.administrators = [
    administrator({
      name: 'Marta Wójcik',
      email: 'marta.wojcik.coaching@ogrody33-krakow.pl',
      status: 'ACTIVE',
      last_used_at: fromNow(-3 * DAY_MS),
      expires_at: null,
      groups: [
        { id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e01', name: 'Ogrody 33 Club' },
        { id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e02', name: 'Ogrody open play' },
      ],
      can_reset_password: true,
    }),
    administrator({ name: 'Tomek K.', email: 'tomek.k@gmail.com', status: 'EXPIRED' }),
  ];
  await signIn(page);
  await page.goto('/administrators');
  await page.getByText('2 groups').click();
  await fitsSideways(page, '/administrators');

  await page.getByRole('button', { name: '+ Add administrator' }).click();
  await page.getByLabel('Name', { exact: true }).fill('Robert');
  await page.getByLabel('Email', { exact: true }).fill('robert.constantin.dinescu@example.com');
  await fitsSideways(page, '/administrators, adding');

  await page.getByRole('button', { name: 'Send invitation', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Done' })).toBeVisible();
  await fitsSideways(page, '/administrators, sent');

  await page.getByRole('button', { name: 'Remove' }).first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await fitsSideways(page, '/administrators, removing');
});

test('Groups and Hand over fit a phone: the table, the choices and the question', async ({
  page,
  club,
}) => {
  const active = (name: string, email: string) =>
    administrator({
      name,
      email,
      status: 'ACTIVE',
      last_used_at: fromNow(-DAY_MS),
      expires_at: null,
    });
  const marta = active('Marta Wójcik', 'marta.wojcik.coaching@ogrody33-krakow.pl');
  club.administrators = [marta, active('Tomek Kowalczykiewicz', 'tomek.kowalczykiewicz@gmail.com')];
  const group = officialGroup({
    name: 'Ogrody 33 Club — wieczorne granie dla wszystkich',
    runBy: marta,
    member_count: 52,
    waiting_count: 12,
    whatsapp_size: 48,
  });
  group.requests = [joinRequest({ nickname: LONGEST_NICKNAME }), ...group.requests.slice(1)];
  club.groups = [group, officialGroup({ name: 'Ogrody open play', member_count: 8 })];
  await signIn(page);
  await page.goto('/groups');
  await expect(page.getByText('52 of 48 · 108%')).toBeVisible();
  await fitsSideways(page, '/groups');
  // With the column heads gone, a bare figure says what it counts.
  const games = page.getByRole('row').nth(1).getByRole('cell').last();
  expect(await games.evaluate((cell) => getComputedStyle(cell, '::before').content)).toMatch(
    /Games/,
  );

  await page.goto(`/groups/${group.id}`);
  await expect(page.getByText(LONGEST_NICKNAME)).toBeVisible();
  await page.getByRole('radio', { name: /Tomek/ }).check();
  await fitsSideways(page, '/groups/<id>');

  await page.getByRole('button', { name: 'Hand over', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await fitsSideways(page, '/groups/<id>, confirming');
});

test("The club's menu, the checklist and Rakieta settings fit a phone", async ({ page, club }) => {
  void club;
  await signIn(page);
  await expect(page.getByRole('list', { name: 'Setup checklist' })).toBeVisible();
  await fitsSideways(page, '/overview');
  await page
    .getByRole('banner')
    .getByRole('button', { name: /Ogrody 33/ })
    .click();
  await expect(
    page.getByRole('banner').getByRole('link', { name: 'Rakieta settings' }),
  ).toBeVisible();
  await fitsSideways(page, '/overview, the menu open');

  await page.goto('/rakieta-settings');
  // Other clubs' courts are on by default, so the distance box is drawn too.
  await expect(page.getByLabel('Distance')).toBeVisible();
  await fitsSideways(page, '/rakieta-settings');
  await page.getByRole('button', { name: 'Leave Rakieta' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await fitsSideways(page, '/rakieta-settings, leaving');
});

test('Courts & prices fits a phone: the table, the grid, the forms and the bands', async ({
  page,
  club,
}) => {
  const one = court({
    name: 'Kort centralny przy wejściu',
    sport: 'PADEL',
    hours: week([1], 17, 22),
  });
  club.raketa.courts = [one, court({ name: 'Court 2', sport: 'TENNIS', offered: false })];
  club.raketa.price('PADEL', 140);
  club.raketa.exceptions = [
    {
      id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e01',
      court_ids: [one.id],
      first_day: dayFromToday(3),
      last_day: dayFromToday(30),
      from_hour: 9,
      until_hour: 12,
      reason: 'Wymiana sztucznej trawy na korcie centralnym',
    },
  ];
  await signIn(page);
  await page.goto('/courts');
  await expect(page.getByRole('checkbox', { name: 'Monday 17:00' })).toBeChecked();
  await fitsSideways(page, '/courts');

  await page.getByRole('button', { name: '+ Add a court' }).click();
  await page.getByRole('button', { name: '+ Add an exception' }).click();
  await page.getByRole('radio', { name: 'Some courts' }).check();
  await page.getByRole('radio', { name: 'Hours on a day' }).check();
  await page
    .getByRole('region', { name: 'Prices' })
    .getByRole('group', { name: 'Padel' })
    .getByRole('button', { name: '+ Add a price band' })
    .click();
  await fitsSideways(page, '/courts, every form open');

  await page.getByRole('button', { name: 'Copy to other courts' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await fitsSideways(page, '/courts, copying');
});

test('Bookings fits a phone: the day, its filters, its rows and each question', async ({
  page,
  club,
}) => {
  const hours = week([1, 2, 3, 4, 5, 6, 7], 7, 23);
  const one = court({ name: 'Kort centralny przy wejściu', sport: 'PADEL', hours });
  club.raketa.courts = [one, court({ name: 'Court 2', sport: 'PADEL', hours })];
  const day = dayFromToday(2);
  const long = club.bookings.add(
    booking({
      court: one,
      day,
      hour: 19,
      booked_from: {
        group_id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e01',
        name: 'Ogrody 33 Club — wieczorne granie dla wszystkich',
        official: true,
      },
    }),
  );
  long.players = long.players.map((player, index) =>
    index === 0 ? { ...player, nickname: LONGEST_NICKNAME } : player,
  );
  club.bookings.add(
    booking({
      court: one,
      day,
      hour: 20,
      stage: 'CALLED_OFF',
      called_off_reason: 'CANCELLED_BY_THE_CLUB',
      cancel_reason: 'DOUBLE_BOOKING',
    }),
  );
  await signIn(page);
  await page.goto(`/bookings?date=${day}`);
  await expect(page.getByRole('rowheader')).toHaveCount(2);
  await expect(page.getByRole('rowheader').first()).toContainText(
    'Kort centralny przy wejściu · indoor',
  );
  await expect(page.getByText(LONGEST_NICKNAME)).toBeVisible();
  await fitsSideways(page, '/bookings');

  await page.getByRole('button', { name: /^Move/ }).click();
  await expect(page.getByRole('dialog').getByRole('radio')).toHaveCount(1);
  await fitsSideways(page, '/bookings, moving');
  await page.getByRole('dialog').getByRole('button', { name: 'Back' }).click();

  // The cancel would move the game to Court 2: the dialog says so and offers to cancel anyway.
  await page.getByRole('button', { name: /^Cancel/ }).click();
  await page.getByRole('dialog').getByRole('radio', { name: 'Repair' }).check();
  await expect(page.getByRole('dialog').getByRole('status')).toContainText(
    'This game moves to Court 2 · indoor',
  );
  await expect(
    page.getByRole('dialog').getByRole('button', { name: 'Cancel the game anyway' }),
  ).toBeVisible();
  await fitsSideways(page, '/bookings, cancelling');
});

test('Overview, once live, fits a phone', async ({ page, club }) => {
  club.raketa.ready();
  await signIn(page);
  await expect(page.getByRole('region', { name: 'Live on Rakieta' })).toBeVisible();
  await fitsSideways(page, '/overview, live');
});

test('Money fits a phone: the month, its totals, its rows and the payouts', async ({
  page,
  club,
}) => {
  club.raketa.payments = 'READY';
  const long = court({ name: 'Kort centralny przy wejściu', sport: 'PADEL' });
  club.money.add(
    moneyRow({
      court: long,
      day: '2026-03-07',
      hour: 18,
      status: 'CALLED_OFF',
      refunded_grosze: 140_00,
    }),
  );
  club.money.add(moneyRow({ court: long, day: '2026-03-09', hour: 19, paid_out: true }));
  club.money.payouts = [
    payout({ amount_grosze: 1_234_50, arrives_at: fromNow(-DAY_MS), status: 'FAILED' }),
    payout({ amount_grosze: 134_00, arrives_at: fromNow(-2 * DAY_MS) }),
  ];
  await signIn(page);
  await page.goto('/money?month=2026-03');
  await expect(page.getByRole('region', { name: 'Payouts' }).getByRole('row')).toHaveCount(3);
  await fitsSideways(page, '/money');
  // With the column heads gone, a bare figure says what it is.
  const net = page.getByRole('row').nth(1).getByRole('cell').nth(4);
  expect(await net.evaluate((cell) => getComputedStyle(cell, '::before').content)).toMatch(/Net/);
});

test("The checklist's Stripe step fits a phone, refused and all", async ({ page, stub, club }) => {
  club.raketa.payments = 'NEEDS_DETAILS';
  await signIn(page);
  stub.on('post', '/api/v1/club/payments/onboarding-link', () => ({
    status: 503,
    body: refusal('payments_unavailable'),
  }));
  await page.getByRole('button', { name: 'Continue with Stripe' }).click();
  await expect(page.getByRole('main').getByRole('alert')).toBeVisible();
  await fitsSideways(page, '/overview, Stripe refused');
});
