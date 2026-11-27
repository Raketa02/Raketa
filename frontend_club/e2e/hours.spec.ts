import type { Locator, Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { court, week } from './stub/courts';

/**
 * **Courts & prices: Weekly hours for Rakieta** (#561, the screens B3, the mechanics §16.5): the
 * hours of an ordinary week each court is offered, on the player's own grid, seven days by
 * sixteen hours from 07:00 to 23:00. A tap or a drag paints them; a save gives the week to one
 * court, to every court of a sport, or, with *Copy to other courts*, to the courts ticked.
 */

async function openHours(page: Page) {
  await signIn(page);
  await page.goto('/courts');
  return page.getByRole('region', { name: 'Weekly hours for Rakieta' });
}

function cell(hours: Locator, name: string) {
  return hours.getByRole('checkbox', { name, exact: true });
}

/** The controls `controls` finds are these, named so, in this order. */
async function namesAre(controls: Locator, names: readonly string[]) {
  await expect(controls).toHaveCount(names.length);
  for (const [index, name] of names.entries()) {
    await expect(controls.nth(index)).toHaveAccessibleName(name);
  }
}

/** Press on one cell and let go on another, passing over the cells between, all on screen. */
async function drag(page: Page, from: Locator, to: Locator, steps = 12) {
  await to.scrollIntoViewIfNeeded();
  await from.scrollIntoViewIfNeeded();
  const a = await from.boundingBox();
  const b = await to.boundingBox();
  if (a === null || b === null) throw new Error('a cell has no box');
  await page.mouse.move(a.x + a.width / 2, a.y + a.height / 2);
  await page.mouse.down();
  await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps });
  await page.mouse.up();
}

test.describe('Weekly hours for Rakieta', () => {
  test('waits for a court', async ({ page, club }) => {
    void club;
    const hours = await openHours(page);
    await expect(hours).toContainText('Add a court first');
    await expect(hours.getByRole('checkbox')).toHaveCount(0);
  });

  test("shows a court's week, and a tap offers an hour or takes it back", async ({
    page,
    stub,
    club,
  }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL', hours: week([1], 17, 19) });
    club.rakieta.courts = [one];
    const hours = await openHours(page);

    await expect(hours.getByRole('checkbox')).toHaveCount(7 * 16);
    await expect(cell(hours, 'Monday 07:00')).not.toBeChecked();
    await expect(cell(hours, 'Monday 17:00')).toBeChecked();
    await expect(cell(hours, 'Monday 18:00')).toBeChecked();
    await expect(cell(hours, 'Sunday 22:00')).not.toBeChecked();
    await expect(hours.getByRole('checkbox', { checked: true })).toHaveCount(2);

    await cell(hours, 'Monday 18:00').click();
    await cell(hours, 'Saturday 09:00').click();
    await expect(cell(hours, 'Monday 18:00')).not.toBeChecked();
    await expect(cell(hours, 'Saturday 09:00')).toBeChecked();
    await hours.getByRole('button', { name: 'Save hours' }).click();

    await expect(hours.getByRole('status')).toHaveText('Hours saved for Court 1.');
    expect(stub.requests('put', '/api/v1/club/rakieta-hours').map((r) => r.body)).toEqual([
      {
        court_ids: [one.id],
        hours: [
          { day: 1, hour: 17 },
          { day: 6, hour: 9 },
        ],
      },
    ]);
  });

  test('a drag paints every hour it passes, and one begun on an offered hour clears them', async ({
    page,
    club,
  }) => {
    club.rakieta.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    const hours = await openHours(page);

    await drag(page, cell(hours, 'Tuesday 08:00'), cell(hours, 'Tuesday 11:00'));
    for (const hour of ['08:00', '09:00', '10:00', '11:00']) {
      await expect(cell(hours, `Tuesday ${hour}`)).toBeChecked();
    }
    await expect(cell(hours, 'Tuesday 12:00')).not.toBeChecked();

    await drag(page, cell(hours, 'Tuesday 09:00'), cell(hours, 'Tuesday 10:00'));
    await expect(cell(hours, 'Tuesday 08:00')).toBeChecked();
    await expect(cell(hours, 'Tuesday 09:00')).not.toBeChecked();
    await expect(cell(hours, 'Tuesday 10:00')).not.toBeChecked();
    await expect(cell(hours, 'Tuesday 11:00')).toBeChecked();
  });

  test('a drag faster than the browser reports still paints every hour it crossed', async ({
    page,
    club,
  }) => {
    club.rakieta.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    const hours = await openHours(page);

    // One move, from Thursday 08:00 straight to Saturday 11:00: the line between is painted.
    await drag(page, cell(hours, 'Thursday 08:00'), cell(hours, 'Saturday 11:00'), 1);
    await expect(hours.getByRole('checkbox', { checked: true })).toHaveCount(4);
    for (const name of ['Thursday 08:00', 'Friday 09:00', 'Friday 10:00', 'Saturday 11:00']) {
      await expect(cell(hours, name)).toBeChecked();
    }
  });

  test('the keyboard walks the grid with the arrows and ticks with Space', async ({
    page,
    club,
  }) => {
    club.rakieta.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    const hours = await openHours(page);

    await cell(hours, 'Monday 07:00').focus();
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('ArrowDown');
    await expect(cell(hours, 'Tuesday 08:00')).toBeFocused();
    await page.keyboard.press('Space');
    await expect(cell(hours, 'Tuesday 08:00')).toBeChecked();
    // One stop in the tab order for the whole grid.
    await expect(hours.getByRole('checkbox').and(hours.locator('[tabindex="0"]'))).toHaveCount(1);
  });

  test("All padel courts gives the same week to each, and another court's is its own", async ({
    page,
    stub,
    club,
  }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL', hours: week([1], 17, 18) });
    const two = court({ name: 'Court 2', sport: 'PADEL', hours: week([2], 17, 18) });
    const tennis = court({ name: 'Kort centralny', sport: 'TENNIS', hours: week([3], 9, 10) });
    club.rakieta.courts = [one, two, tennis];
    const hours = await openHours(page);

    const picker = hours.getByRole('radiogroup', { name: 'Courts to set' });
    await namesAre(picker.getByRole('radio'), [
      'Court 1',
      'Court 2',
      'Kort centralny',
      'All padel courts',
    ]);
    await expect(picker.getByRole('radio', { name: 'Court 1' })).toBeChecked();

    await picker.getByRole('radio', { name: 'Kort centralny' }).check();
    await expect(cell(hours, 'Wednesday 09:00')).toBeChecked();
    await expect(cell(hours, 'Monday 17:00')).not.toBeChecked();

    await picker.getByRole('radio', { name: 'All padel courts' }).check();
    await expect(hours).toContainText("These courts don't all have the same hours.");
    await cell(hours, 'Friday 20:00').click();
    await hours.getByRole('button', { name: 'Save hours' }).click();

    await expect(hours.getByRole('status')).toHaveText('Hours saved for Court 1 and Court 2.');
    const [saved] = stub.requests('put', '/api/v1/club/rakieta-hours');
    expect(saved?.body.court_ids).toEqual([one.id, two.id]);
    expect(club.rakieta.courts.map((each) => each.hours.length)).toEqual([2, 2, 1]);
    await expect(hours).not.toContainText("These courts don't all have the same hours.");
  });

  test("Copy to other courts gives one court's week to the courts ticked", async ({
    page,
    stub,
    club,
  }) => {
    const one = court({ name: 'Court 1', sport: 'PADEL', hours: week([1, 2], 17, 22) });
    const two = court({ name: 'Court 2', sport: 'PADEL' });
    const three = court({ name: 'Court 3', sport: 'TENNIS', offered: false });
    club.rakieta.courts = [one, two, three];
    const hours = await openHours(page);

    await hours.getByRole('button', { name: 'Copy to other courts' }).click();
    const dialog = page.getByRole('dialog', { name: "Copy Court 1's week" });
    await namesAre(dialog.getByRole('checkbox'), ['Court 2', 'Court 3']);
    await dialog.getByRole('checkbox', { name: 'Court 3' }).check();
    await dialog.getByRole('button', { name: 'Copy' }).click();

    await expect(hours.getByRole('status')).toHaveText('Hours saved for Court 1 and Court 3.');
    const [saved] = stub.requests('put', '/api/v1/club/rakieta-hours');
    expect(saved?.body.court_ids).toEqual([one.id, three.id]);
    expect(saved?.body.hours).toHaveLength(10);
    expect(club.rakieta.courts[2]?.hours).toEqual(one.hours);
  });

  test('a court deleted elsewhere is said over the grid, which is drawn again', async ({
    page,
    stub,
    club,
  }) => {
    club.rakieta.courts = [court({ name: 'Court 1', sport: 'PADEL' })];
    stub.on('put', '/api/v1/club/rakieta-hours', () => ({
      status: 404,
      body: refusal('court_not_found'),
    }));
    const hours = await openHours(page);
    await cell(hours, 'Monday 07:00').click();
    club.rakieta.courts = [];
    await hours.getByRole('button', { name: 'Save hours' }).click();

    await expect(hours.getByRole('alert')).toHaveText("One of those courts isn't yours any more.");
    await expect(hours).toContainText('Add a court first');
  });
});
