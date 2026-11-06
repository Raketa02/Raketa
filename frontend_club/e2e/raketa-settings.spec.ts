import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';

/**
 * **Raketa settings** (#561, #674, the screens B5, the mechanics §16.6): one form, every setting
 * the club confirms: the release lead, the cut-off, other clubs' courts and the pause. Every club
 * works one way (Q121), so there is no way to choose. The first save confirms the settings, the
 * setup checklist's last step.
 */

const OTHER_CLUBS_SWITCH = "Offer our groups other clubs' courts when ours are full";

async function openSettings(page: Page) {
  await signIn(page);
  await page.goto('/raketa-settings');
  await expect(page.getByRole('heading', { name: 'Raketa settings', level: 1 })).toBeVisible();
}

test.describe('Raketa settings', () => {
  test("a new club sees every setting at its default, other clubs' courts on within 10 km, and no way to choose", async ({
    page,
    club,
  }) => {
    void club;
    await openSettings(page);

    await expect(page.getByLabel('Release lead')).toHaveValue('3');
    await expect(page.getByLabel('Free-cancellation cut-off')).toHaveValue('24');
    // Only Raketa is the one way (Q121): nothing to choose, and nothing only another way asked.
    await expect(page.getByRole('radiogroup')).toHaveCount(0);
    await expect(page.getByRole('main').getByRole('radio')).toHaveCount(0);
    for (const gone of ['How you work with Raketa', 'Instant', 'On request']) {
      await expect(page.getByText(gone)).toHaveCount(0);
    }
    await expect(page.getByLabel('Minimum notice')).toHaveCount(0);
    await expect(page.getByLabel('Time to confirm')).toHaveCount(0);

    // On by default (Q128), and only at an hour the club's own courts are full.
    const otherClubs = page.getByRole('switch', { name: OTHER_CLUBS_SWITCH });
    await expect(otherClubs).toBeChecked();
    await expect(otherClubs).toHaveAccessibleDescription(
      "At an hour your courts are full, your groups are also offered other clubs' courts within 10 km.",
    );
    await expect(page.getByLabel('Distance')).toHaveValue('10');
    // The desk checks nobody in (ADR-0195): these two are the only switches.
    await expect(page.getByRole('main').getByRole('switch')).toHaveCount(2);
    await expect(page.getByRole('switch', { name: 'Pause Raketa bookings' })).not.toBeChecked();
    await expect(page.getByRole('button', { name: 'Confirm settings' })).toBeVisible();
  });

  test('Confirm settings sends every setting and nothing else, and the checklist moves on', async ({
    page,
    stub,
    club,
  }) => {
    await openSettings(page);
    await page.getByLabel('Release lead').fill('1');
    await page.getByRole('button', { name: 'Confirm settings' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Settings confirmed.');
    expect(stub.requests('put', '/api/v1/club/raketa-settings').map((r) => r.body)).toEqual([
      {
        release_lead_days: 1,
        cut_off_hours: 24,
        other_clubs_courts: { offered: true, within_km: 10 },
        paused: false,
      },
    ]);
    expect(club.raketa.confirmed).toBe(true);
    await expect(page.getByRole('button', { name: 'Save settings' })).toBeVisible();

    await page.getByRole('navigation').getByRole('link', { name: 'Overview' }).click();
    const steps = page.getByRole('list', { name: 'Setup checklist' }).locator('[data-state]');
    await expect(steps).toHaveText(['not started', 'to do', 'locked', 'done ✓']);
  });

  test('a confirmed club saves its settings as they stand', async ({ page, stub, club }) => {
    club.raketa.confirmed = true;
    club.raketa.settings.release_lead_days = 5;
    await openSettings(page);

    await expect(page.getByLabel('Release lead')).toHaveValue('5');
    await page.getByLabel('Free-cancellation cut-off').fill('12');
    await page.getByRole('button', { name: 'Save settings' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Settings saved.');
    expect(stub.requests('put', '/api/v1/club/raketa-settings').map((r) => r.body)).toEqual([
      {
        release_lead_days: 5,
        cut_off_hours: 12,
        other_clubs_courts: { offered: true, within_km: 10 },
        paused: false,
      },
    ]);
  });

  test("other clubs' courts asks how far only while it is on", async ({ page, stub, club }) => {
    void club;
    await openSettings(page);
    const otherClubs = page.getByRole('switch', { name: OTHER_CLUBS_SWITCH });
    await otherClubs.uncheck();
    await expect(page.getByLabel('Distance')).toHaveCount(0);

    await otherClubs.check();
    await expect(page.getByLabel('Distance')).toHaveValue('10');
    await page.getByLabel('Distance').fill('15');
    await page.getByRole('switch', { name: 'Pause Raketa bookings' }).check();
    await expect(page.getByText('No new games are built on your courts.')).toBeVisible();
    await page.getByRole('button', { name: 'Confirm settings' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Settings confirmed.');
    expect(stub.requests('put', '/api/v1/club/raketa-settings')[0]?.body).toMatchObject({
      other_clubs_courts: { offered: true, within_km: 15 },
      paused: true,
    });
    await expect(otherClubs).toHaveAccessibleDescription(
      "At an hour your courts are full, your groups are also offered other clubs' courts within 15 km.",
    );
  });

  test("switched off, other clubs' courts keeps its distance for when it is back on", async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.confirmed = true;
    club.raketa.settings.other_clubs_courts = { offered: true, within_km: 25 };
    await openSettings(page);
    const otherClubs = page.getByRole('switch', { name: OTHER_CLUBS_SWITCH });
    await otherClubs.uncheck();
    await page.getByRole('button', { name: 'Save settings' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Settings saved.');
    expect(stub.requests('put', '/api/v1/club/raketa-settings')[0]?.body).toMatchObject({
      other_clubs_courts: { offered: false, within_km: 25 },
    });
    await page.reload();
    await expect(otherClubs).not.toBeChecked();
    await otherClubs.check();
    await expect(page.getByLabel('Distance')).toHaveValue('25');
  });

  test('a setting out of its range is refused under it, by this site or the server', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await openSettings(page);
    await page.getByLabel('Release lead').fill('20');
    await page.getByLabel('Free-cancellation cut-off').fill('');
    await page.getByRole('button', { name: 'Confirm settings' }).click();

    await expect(page.getByText('A release lead is 1 to 13 days.')).toBeVisible();
    await expect(page.getByLabel('Release lead')).toHaveAttribute('aria-invalid', 'true');
    await expect(page.getByText('A cut-off is 0 to 72 hours.')).toBeVisible();
    expect(stub.requests('put', '/api/v1/club/raketa-settings')).toEqual([]);

    stub.on('put', '/api/v1/club/raketa-settings', () => ({
      status: 400,
      body: refusal('setting_out_of_range', 'cut_off_hours', { least: 0, most: 72 }),
    }));
    await page.getByLabel('Release lead').fill('4');
    await page.getByLabel('Free-cancellation cut-off').fill('48');
    await page.getByRole('button', { name: 'Confirm settings' }).click();
    await expect(page.getByText('A cut-off is 0 to 72 hours.')).toBeVisible();
    await expect(page.getByRole('main').getByRole('status')).toHaveCount(0);
  });

  test('Leave Raketa explains leaving, and starts it with a pause', async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.confirmed = true;
    await openSettings(page);

    await page.getByRole('button', { name: 'Leave Raketa' }).click();
    const dialog = page.getByRole('dialog', { name: 'Leave Raketa?' });
    await expect(dialog).toContainText('Leaving starts with a pause');
    await dialog.getByRole('button', { name: 'Pause Raketa bookings' }).click();

    await expect(dialog).toBeHidden();
    await expect(page.getByRole('switch', { name: 'Pause Raketa bookings' })).toBeChecked();
    expect(stub.requests('put', '/api/v1/club/raketa-settings').map((r) => r.body)).toEqual([
      {
        release_lead_days: 3,
        cut_off_hours: 24,
        other_clubs_courts: { offered: true, within_km: 10 },
        paused: true,
      },
    ]);

    await page.getByRole('button', { name: 'Leave Raketa' }).click();
    await expect(dialog).toContainText('Raketa bookings are paused.');
    await expect(dialog.getByRole('button', { name: 'Pause Raketa bookings' })).toHaveCount(0);
    await dialog.getByRole('button', { name: 'Close' }).click();
    await expect(dialog).toBeHidden();
  });

  test('until the settings are confirmed there is nothing to leave, and no pause to confirm them', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await openSettings(page);
    await page.getByRole('button', { name: 'Leave Raketa' }).click();

    const dialog = page.getByRole('dialog', { name: 'Leave Raketa?' });
    await expect(dialog).toContainText("Your settings aren't confirmed yet");
    await expect(dialog.getByRole('button', { name: 'Pause Raketa bookings' })).toHaveCount(0);
    await dialog.getByRole('button', { name: 'Close' }).click();
    expect(stub.requests('put', '/api/v1/club/raketa-settings')).toEqual([]);
    expect(club.raketa.confirmed).toBe(false);
  });

  test('a pause nobody answered is said beside the link, and nothing changes', async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.confirmed = true;
    stub.on('put', '/api/v1/club/raketa-settings', () => ({ status: 'drop' }));
    await openSettings(page);
    await page.getByRole('button', { name: 'Leave Raketa' }).click();
    await page
      .getByRole('dialog', { name: 'Leave Raketa?' })
      .getByRole('button', { name: 'Pause Raketa bookings' })
      .click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "We couldn't reach the server. Try again in a moment.",
    );
    await expect(page.getByRole('switch', { name: 'Pause Raketa bookings' })).not.toBeChecked();
  });
});
