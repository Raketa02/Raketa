import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { dayFromToday } from './stub/clock';
import { court } from './stub/courts';

/**
 * **Courts & prices: the courts** (#561, the screens B3, the mechanics §16.4): the courts the
 * club offers Rakieta, each with one sport, indoor or outdoor, added, edited, switched off and on, and
 * deleted while nothing is booked on it.
 */

async function openCourts(page: Page) {
  await signIn(page);
  await page.goto('/courts');
  await expect(page.getByRole('heading', { name: 'Courts & prices', level: 1 })).toBeVisible();
  return page.getByRole('region', { name: 'Courts', exact: true });
}

function rowOf(page: Page, name: string) {
  return page.getByRole('row').filter({ has: page.getByRole('rowheader', { name, exact: true }) });
}

test.describe('Courts', () => {
  test('a club with none is asked to add one, and the court it adds is listed', async ({
    page,
    stub,
    club,
  }) => {
    const courts = await openCourts(page);
    await expect(courts).toContainText('No courts yet.');

    await courts.getByRole('button', { name: '+ Add a court' }).click();
    await courts.getByLabel('Name').fill('  Kort   centralny ');
    // The club's own sports, and nothing else.
    await expect(courts.getByRole('radiogroup', { name: 'Sport' }).getByRole('radio')).toHaveCount(
      2,
    );
    await courts.getByRole('radio', { name: 'Tennis' }).check();
    await courts.getByRole('radio', { name: 'Outdoor' }).check();
    await courts.getByRole('button', { name: 'Add court' }).click();

    await expect(rowOf(page, 'Kort centralny').getByRole('cell')).toHaveText([
      'Tennis',
      'Outdoor',
      'on',
      /Switch off\s*Edit/,
    ]);
    expect(stub.requests('post', '/api/v1/club/courts').map((r) => r.body)).toEqual([
      { name: 'Kort centralny', sport: 'TENNIS', indoor: false },
    ]);
    expect(club.rakieta.courts.map((each) => each.name)).toEqual(['Kort centralny']);
    await expect(courts.getByLabel('Name')).toHaveCount(0);
  });

  test('a court the site would refuse is said under its fields, and nothing is sent', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    const courts = await openCourts(page);
    await courts.getByRole('button', { name: '+ Add a court' }).click();
    await courts.getByRole('button', { name: 'Add court' }).click();

    await expect(courts.getByText("A court's name is 1 to 40 characters.")).toBeVisible();
    await expect(courts.getByText("Choose the court's sport.")).toBeVisible();
    await expect(courts.getByText('Say whether it is indoor or outdoor.')).toBeVisible();
    expect(stub.requests('post', '/api/v1/club/courts')).toEqual([]);

    await courts.getByRole('button', { name: 'Cancel' }).click();
    await expect(courts.getByLabel('Name')).toHaveCount(0);
  });

  test('a name another court has is refused under it, as the server says', async ({
    page,
    club,
  }) => {
    club.rakieta.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    const courts = await openCourts(page);
    await courts.getByRole('button', { name: '+ Add a court' }).click();
    await courts.getByLabel('Name').fill('court 1');
    await courts.getByRole('radio', { name: 'Padel' }).check();
    await courts.getByRole('radio', { name: 'Indoor' }).check();
    await courts.getByRole('button', { name: 'Add court' }).click();

    await expect(courts.getByText('Another of your courts has this name.')).toBeVisible();
    await expect(courts.getByLabel('Name')).toHaveAttribute('aria-invalid', 'true');
    expect(club.rakieta.courts).toHaveLength(1);
  });

  test('Edit changes a court in place, keeping whether it is offered', async ({
    page,
    stub,
    club,
  }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL', offered: false });
    club.rakieta.courts = [one];
    const courts = await openCourts(page);
    await rowOf(page, 'Court 1').getByRole('button', { name: 'Edit' }).click();

    await expect(courts.getByRole('heading', { name: 'Edit Court 1' })).toBeVisible();
    await expect(courts.getByLabel('Name')).toHaveValue('Court 1');
    await expect(courts.getByRole('radio', { name: 'Padel' })).toBeChecked();
    await expect(courts.getByRole('radio', { name: 'Indoor' })).toBeChecked();
    await courts.getByLabel('Name').fill('Court 2');
    await courts.getByRole('radio', { name: 'Outdoor' }).check();
    await courts.getByRole('button', { name: 'Save' }).click();

    await expect(rowOf(page, 'Court 2').getByRole('cell')).toHaveText([
      'Padel',
      'Outdoor',
      'off',
      /Switch on\s*Edit/,
    ]);
    expect(stub.requests('put', '/api/v1/club/courts/{court_id}').map((r) => r.body)).toEqual([
      { name: 'Court 2', sport: 'PADEL', indoor: false, offered: false },
    ]);
    expect(stub.requests('put', '/api/v1/club/courts/{court_id}')[0]?.params.court_id).toBe(one.id);
  });

  test('a court with a booking ahead keeps its sport, and the form says why', async ({
    page,
    club,
  }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL' });
    club.rakieta.courts = [one];
    club.bookings.book(one, dayFromToday(2), 18);
    const courts = await openCourts(page);
    await rowOf(page, 'Court 1').getByRole('button', { name: 'Edit' }).click();
    await courts.getByRole('radio', { name: 'Tennis' }).check();
    await courts.getByRole('button', { name: 'Save' }).click();

    await expect(courts.getByRole('alert')).toHaveText(
      'Court 1 has a booking ahead, so it keeps its sport until that game is played.',
    );
    expect(club.rakieta.courts[0]?.sport).toBe('PADEL');
  });

  test('Switch off asks first and says what it means; Switch on is at once', async ({
    page,
    stub,
    club,
  }) => {
    club.rakieta.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    await openCourts(page);
    await rowOf(page, 'Court 1').getByRole('button', { name: 'Switch off' }).click();

    const dialog = page.getByRole('dialog', { name: 'Switch Court 1 off?' });
    await expect(dialog).toContainText('Games already booked on it are played as booked');
    await dialog.getByRole('button', { name: 'Switch off' }).click();

    await expect(rowOf(page, 'Court 1').getByRole('cell').nth(2)).toHaveText('off');
    expect(stub.requests('put', '/api/v1/club/courts/{court_id}').map((r) => r.body)).toEqual([
      { name: 'Court 1', sport: 'PADEL', indoor: true, offered: false },
    ]);

    await rowOf(page, 'Court 1').getByRole('button', { name: 'Switch on' }).click();
    await expect(rowOf(page, 'Court 1').getByRole('cell').nth(2)).toHaveText('on');
    expect(stub.requests('put', '/api/v1/club/courts/{court_id}').at(-1)?.body.offered).toBe(true);
  });

  test('Delete asks first, and a court with a booking ahead is switched off instead', async ({
    page,
    stub,
    club,
  }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL' });
    const two = court({ name: 'Court 2', sport: 'PADEL' });
    club.rakieta.courts = [one, two];
    club.bookings.book(two, dayFromToday(1), 19);
    const courts = await openCourts(page);

    await rowOf(page, 'Court 2').getByRole('button', { name: 'Edit' }).click();
    await courts.getByRole('button', { name: 'Delete court' }).click();
    const dialog = page.getByRole('dialog', { name: 'Delete Court 2?' });
    await dialog.getByRole('button', { name: 'Delete' }).click();
    await expect(courts.getByRole('alert')).toHaveText(
      "Court 2 has a booking ahead, so it can't be deleted. Switch it off instead.",
    );
    expect(club.rakieta.courts).toHaveLength(2);

    await rowOf(page, 'Court 1').getByRole('button', { name: 'Edit' }).click();
    await courts.getByRole('button', { name: 'Delete court' }).click();
    await page
      .getByRole('dialog', { name: 'Delete Court 1?' })
      .getByRole('button', {
        name: 'Delete',
      })
      .click();
    await expect(rowOf(page, 'Court 1')).toHaveCount(0);
    expect(stub.requests('delete', '/api/v1/club/courts/{court_id}').map((r) => r.params)).toEqual([
      { court_id: two.id },
      { court_id: one.id },
    ]);
  });

  test('a court gone elsewhere is said over the table, which is drawn again', async ({
    page,
    club,
  }) => {
    club.rakieta.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    await openCourts(page);
    // Deleted from another browser while this page was open.
    club.rakieta.courts = [];
    await rowOf(page, 'Court 1').getByRole('button', { name: 'Switch off' }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Switch off' }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "Court 1 isn't one of your courts any more.",
    );
    await expect(rowOf(page, 'Court 1')).toHaveCount(0);
  });

  test('a sport the club stopped offering is refused under the sport, as the server says', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    stub.on('post', '/api/v1/club/courts', () => ({
      status: 400,
      body: refusal('court_sport_not_offered', 'sport'),
    }));
    const courts = await openCourts(page);
    await courts.getByRole('button', { name: '+ Add a court' }).click();
    await courts.getByLabel('Name').fill('Court 1');
    await courts.getByRole('radio', { name: 'Tennis' }).check();
    await courts.getByRole('radio', { name: 'Indoor' }).check();
    await courts.getByRole('button', { name: 'Add court' }).click();

    await expect(
      courts
        .getByRole('radiogroup', { name: 'Sport' })
        .and(courts.locator('[aria-invalid="true"]')),
    ).toHaveCount(1);
    await expect(
      courts.getByText('Your club no longer offers that sport. Tick it on Details first.'),
    ).toBeVisible();
  });
});
