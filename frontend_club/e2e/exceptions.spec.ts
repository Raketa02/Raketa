import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { court, dayFromToday } from './stub/courts';

/**
 * **Courts & prices: Exceptions** (#561, the screens B3, the mechanics §16.5): hours the club
 * closes without touching its weekly pattern — a day, several, or some hours on a day, on every
 * court or some — with a reason for its own records. Refused over a booking, which the club
 * cancels instead, and the refusal leads to it.
 */

async function openExceptions(page: Page) {
  await signIn(page);
  await page.goto('/courts');
  return page.getByRole('region', { name: 'Exceptions' });
}

function rowOf(page: Page, reason: string) {
  return page
    .getByRole('region', { name: 'Exceptions' })
    .getByRole('row')
    .filter({ has: page.getByRole('rowheader', { name: reason, exact: true }) });
}

test.describe('Exceptions', () => {
  test('lists what is closed: why, when and which courts', async ({ page, club }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL' });
    const two = court({ name: 'Court 2', sport: 'PADEL' });
    club.raketa.courts = [one, two];
    club.raketa.exceptions = [
      {
        id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e01',
        court_ids: null,
        first_day: '2026-10-04',
        last_day: '2026-10-05',
        from_hour: null,
        until_hour: null,
        reason: 'Tournament',
      },
      {
        id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e02',
        court_ids: [two.id],
        first_day: '2026-10-12',
        last_day: '2026-10-12',
        from_hour: 9,
        until_hour: 12,
        reason: 'Repair',
      },
      {
        id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e03',
        court_ids: [one.id, two.id],
        first_day: '2026-10-30',
        last_day: '2026-11-02',
        from_hour: null,
        until_hour: null,
        reason: 'All Saints',
      },
    ];
    const exceptions = await openExceptions(page);

    await expect(exceptions.getByRole('rowheader')).toHaveText([
      'Tournament',
      'Repair',
      'All Saints',
    ]);
    await expect(rowOf(page, 'Tournament').getByRole('cell')).toHaveText([
      '4–5 Oct',
      'All courts',
      'Remove',
    ]);
    await expect(rowOf(page, 'Repair').getByRole('cell')).toHaveText([
      '12 Oct · 09:00–12:00',
      'Court 2',
      'Remove',
    ]);
    await expect(rowOf(page, 'All Saints').getByRole('cell')).toHaveText([
      '30 Oct – 2 Nov',
      'Court 1, Court 2',
      'Remove',
    ]);
  });

  test('a day on every court, added and listed', async ({ page, stub, club }) => {
    club.raketa.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    const exceptions = await openExceptions(page);
    await expect(exceptions).toContainText('Nothing closed.');

    const day = dayFromToday(5);
    await exceptions.getByRole('button', { name: '+ Add an exception' }).click();
    await expect(exceptions.getByRole('radio', { name: 'All courts' })).toBeChecked();
    await expect(exceptions.getByRole('radio', { name: 'A day', exact: true })).toBeChecked();
    await exceptions.getByLabel('Day', { exact: true }).fill(day);
    await exceptions.getByLabel('Reason').fill(' Club   championship ');
    await exceptions.getByRole('button', { name: 'Add exception' }).click();

    await expect(rowOf(page, 'Club championship')).toHaveCount(1);
    expect(stub.requests('post', '/api/v1/club/exceptions').map((r) => r.body)).toEqual([
      {
        court_ids: null,
        first_day: day,
        last_day: day,
        from_hour: null,
        until_hour: null,
        reason: 'Club championship',
      },
    ]);
    await expect(exceptions.getByLabel('Reason')).toHaveCount(0);
  });

  test('some hours on a day, on the courts ticked', async ({ page, stub, club }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL' });
    const two = court({ name: 'Court 2', sport: 'PADEL' });
    club.raketa.courts = [one, two];
    const exceptions = await openExceptions(page);

    const day = dayFromToday(3);
    await exceptions.getByRole('button', { name: '+ Add an exception' }).click();
    await exceptions.getByRole('radio', { name: 'Some courts' }).check();
    await exceptions.getByRole('checkbox', { name: 'Court 2' }).check();
    await exceptions.getByRole('radio', { name: 'Hours on a day' }).check();
    await exceptions.getByLabel('Day', { exact: true }).fill(day);
    await exceptions.getByLabel('From').selectOption('09:00');
    await exceptions.getByLabel('Until').selectOption('12:00');
    await exceptions.getByLabel('Reason').fill('Repair');
    await exceptions.getByRole('button', { name: 'Add exception' }).click();

    await expect(rowOf(page, 'Repair').getByRole('cell').nth(1)).toHaveText('Court 2');
    expect(stub.requests('post', '/api/v1/club/exceptions')[0]?.body).toEqual({
      court_ids: [two.id],
      first_day: day,
      last_day: day,
      from_hour: 9,
      until_hour: 12,
      reason: 'Repair',
    });
  });

  test('several days run from the first to the last', async ({ page, stub, club }) => {
    club.raketa.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    const exceptions = await openExceptions(page);

    await exceptions.getByRole('button', { name: '+ Add an exception' }).click();
    await exceptions.getByRole('radio', { name: 'Several days' }).check();
    await exceptions.getByLabel('First day').fill(dayFromToday(7));
    await exceptions.getByLabel('Last day').fill(dayFromToday(9));
    await exceptions.getByLabel('Reason').fill('Holiday');
    await exceptions.getByRole('button', { name: 'Add exception' }).click();

    await expect(rowOf(page, 'Holiday')).toHaveCount(1);
    expect(stub.requests('post', '/api/v1/club/exceptions')[0]?.body).toMatchObject({
      first_day: dayFromToday(7),
      last_day: dayFromToday(9),
    });
  });

  test('what the site would refuse is said under its field, and nothing is sent', async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    const exceptions = await openExceptions(page);
    await exceptions.getByRole('button', { name: '+ Add an exception' }).click();
    await exceptions.getByRole('radio', { name: 'Some courts' }).check();
    await exceptions.getByRole('radio', { name: 'Several days' }).check();
    await exceptions.getByLabel('First day').fill(dayFromToday(4));
    await exceptions.getByLabel('Last day').fill(dayFromToday(2));
    await exceptions.getByRole('button', { name: 'Add exception' }).click();

    await expect(exceptions.getByText('Give a reason, up to 80 characters.')).toBeVisible();
    await expect(exceptions.getByText("The last day can't come before the first.")).toBeVisible();
    await expect(exceptions.getByText('Tick at least one court.')).toBeVisible();

    await exceptions.getByRole('radio', { name: 'Hours on a day' }).check();
    await exceptions.getByLabel('Day', { exact: true }).fill(dayFromToday(-1));
    await exceptions.getByLabel('From').selectOption('12:00');
    await exceptions.getByLabel('Until').selectOption('09:00');
    await exceptions.getByRole('button', { name: 'Add exception' }).click();
    await expect(exceptions.getByText('That day is over already.')).toBeVisible();
    await expect(
      exceptions.getByText('Choose hours between 07:00 and 23:00, ending after they start.'),
    ).toBeVisible();
    expect(stub.requests('post', '/api/v1/club/exceptions')).toEqual([]);
  });

  test('closing an hour a game is booked on is refused, with the way to the booking', async ({
    page,
    club,
  }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL' });
    const two = court({ name: 'Court 2', sport: 'PADEL' });
    club.raketa.courts = [one, two];
    const day = dayFromToday(6);
    const booking = club.raketa.book(two, day, 18);
    const exceptions = await openExceptions(page);

    await exceptions.getByRole('button', { name: '+ Add an exception' }).click();
    await exceptions.getByRole('radio', { name: 'Hours on a day' }).check();
    await exceptions.getByLabel('Day', { exact: true }).fill(day);
    await exceptions.getByLabel('From').selectOption('17:00');
    await exceptions.getByLabel('Until').selectOption('20:00');
    await exceptions.getByLabel('Reason').fill('Repair');
    await exceptions.getByRole('button', { name: 'Add exception' }).click();

    const refused = exceptions.getByRole('alert');
    await expect(refused).toContainText('Court 2 is booked then — cancel the booking first.');
    await expect(refused.getByRole('link', { name: 'See the booking' })).toHaveAttribute(
      'href',
      `/bookings?date=${day}&booking=${booking.id}`,
    );
    expect(club.raketa.exceptions).toEqual([]);
    // What the desk typed is still there to change.
    await expect(exceptions.getByLabel('Reason')).toHaveValue('Repair');
  });

  test('Remove opens the hours again', async ({ page, stub, club }) => {
    club.raketa.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    club.raketa.exceptions = [
      {
        id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e01',
        court_ids: null,
        first_day: dayFromToday(3),
        last_day: dayFromToday(3),
        from_hour: null,
        until_hour: null,
        reason: 'Tournament',
      },
    ];
    await openExceptions(page);
    await rowOf(page, 'Tournament').getByRole('button', { name: 'Remove' }).click();

    await expect(rowOf(page, 'Tournament')).toHaveCount(0);
    expect(
      stub.requests('delete', '/api/v1/club/exceptions/{exception_id}').map((r) => r.params),
    ).toEqual([{ exception_id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e01' }]);
  });

  test("the server's refusal lands under the field it names, or over the form", async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    stub.on('post', '/api/v1/club/exceptions', () => ({
      status: 400,
      body: refusal('exception_in_the_past', 'days'),
    }));
    const exceptions = await openExceptions(page);
    await exceptions.getByRole('button', { name: '+ Add an exception' }).click();
    await exceptions.getByLabel('Day', { exact: true }).fill(dayFromToday(1));
    await exceptions.getByLabel('Reason').fill('Tournament');
    await exceptions.getByRole('button', { name: 'Add exception' }).click();
    await expect(exceptions.getByText('That day is over already.')).toBeVisible();
    await expect(exceptions.getByLabel('Day', { exact: true })).toHaveAttribute(
      'aria-invalid',
      'true',
    );

    stub.on('post', '/api/v1/club/exceptions', () => ({
      status: 404,
      body: refusal('court_not_found'),
    }));
    await exceptions.getByLabel('Reason').fill('Tournament final');
    await exceptions.getByRole('button', { name: 'Add exception' }).click();
    await expect(exceptions.getByRole('alert')).toHaveText(
      "One of those courts isn't yours any more.",
    );
  });

  test('an exception removed elsewhere is said, and the list is drawn again', async ({
    page,
    club,
  }) => {
    club.raketa.exceptions = [
      {
        id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e01',
        court_ids: null,
        first_day: dayFromToday(3),
        last_day: dayFromToday(3),
        from_hour: null,
        until_hour: null,
        reason: 'Tournament',
      },
    ];
    const exceptions = await openExceptions(page);
    club.raketa.exceptions = [];
    await rowOf(page, 'Tournament').getByRole('button', { name: 'Remove' }).click();

    await expect(exceptions.getByRole('alert')).toHaveText('That exception was removed already.');
    await expect(rowOf(page, 'Tournament')).toHaveCount(0);
  });
});
