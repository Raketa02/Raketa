import { expect, signIn, test } from './fixtures';
import { administrator, DAY_MS, fromNow, officialGroup } from './stub/club';
import { court, dayFromToday, week } from './stub/courts';

/** **Every page works at phone width** (#500 story 95): nothing scrolls sideways at 360 px. */

test.use({ viewport: { width: 360, height: 780 } });

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
  void club;
  await signIn(page);
  for (const path of [
    '/overview',
    '/courts',
    '/groups',
    '/administrators',
    '/details',
    '/raketa-settings',
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
  await page.getByRole('radio', { name: /Tomek/ }).check();
  await fitsSideways(page, '/groups/<id>');

  await page.getByRole('button', { name: 'Hand over', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await fitsSideways(page, '/groups/<id>, confirming');
});

test("The club's menu, the checklist and Raketa settings fit a phone", async ({ page, club }) => {
  club.raketa.way = 'ON_REQUEST';
  await signIn(page);
  await expect(page.getByRole('list', { name: 'Setup checklist' })).toBeVisible();
  await fitsSideways(page, '/overview');
  await page
    .getByRole('banner')
    .getByRole('button', { name: /Ogrody 33/ })
    .click();
  await expect(
    page.getByRole('banner').getByRole('link', { name: 'Raketa settings' }),
  ).toBeVisible();
  await fitsSideways(page, '/overview, the menu open');

  await page.goto('/raketa-settings');
  await page
    .getByRole('switch', { name: "Offer our groups other clubs' courts when ours are full" })
    .check();
  await fitsSideways(page, '/raketa-settings');
  await page.getByRole('button', { name: 'Leave Raketa' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await fitsSideways(page, '/raketa-settings, leaving');
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
