import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';

/**
 * **Raketa settings** (#561, the screens B5, the mechanics §16.3 and §16.6): one form, the way
 * the club works with Raketa and every setting it confirms. The way and the settings are two
 * saves at the backend, sent in that order; the first save of the settings confirms them, the
 * setup checklist's last step.
 */

async function openSettings(page: Page) {
  await signIn(page);
  await page.goto('/raketa-settings');
  await expect(page.getByRole('heading', { name: 'Raketa settings', level: 1 })).toBeVisible();
}

test.describe('Raketa settings', () => {
  test('a new club sees the three ways explained, and the settings at their defaults', async ({
    page,
    club,
  }) => {
    void club;
    await openSettings(page);

    const ways = page.getByRole('radiogroup', { name: 'How you work with Raketa' });
    await expect(ways.getByRole('radio')).toHaveCount(3);
    for (const way of ['Only Raketa', 'Instant', 'On request']) {
      await expect(ways.getByRole('radio', { name: way })).not.toBeChecked();
    }
    await expect(ways.getByRole('radio', { name: 'On request' })).toHaveAccessibleDescription(
      /You confirm each full game within your time to confirm\. The players’ shares are held when you do and taken at your cut-off\./,
    );
    await expect(ways).toContainText('A change applies to hours not yet booked.');

    // Only the cut-off matters until a way is chosen.
    await expect(page.getByLabel('Free-cancellation cut-off')).toHaveValue('24');
    await expect(page.getByLabel('Release lead')).toHaveCount(0);
    await expect(page.getByLabel('Minimum notice')).toHaveCount(0);
    await expect(page.getByLabel('Time to confirm')).toHaveCount(0);

    await ways.getByRole('radio', { name: 'Only Raketa' }).check();
    await expect(page.getByLabel('Release lead')).toHaveValue('3');
    await expect(page.getByLabel('Minimum notice')).toHaveCount(0);

    await ways.getByRole('radio', { name: 'On request' }).check();
    await expect(page.getByLabel('Release lead')).toHaveCount(0);
    await expect(page.getByLabel('Minimum notice')).toHaveValue('2');
    await expect(page.getByLabel('Time to confirm')).toHaveValue('30');

    await expect(
      page.getByRole('switch', { name: "Offer our groups other clubs' courts when ours are full" }),
    ).not.toBeChecked();
    // The desk checks nobody in (ADR-0195): these two are the only switches.
    await expect(page.getByRole('main').getByRole('switch')).toHaveCount(2);
    await expect(page.getByRole('switch', { name: 'Pause Raketa bookings' })).not.toBeChecked();
    await expect(page.getByRole('button', { name: 'Confirm settings' })).toBeVisible();
  });

  test('Confirm settings saves the way, then every setting, and the checklist moves on', async ({
    page,
    stub,
    club,
  }) => {
    await openSettings(page);
    await page.getByRole('radio', { name: 'Instant' }).check();
    await page.getByLabel('Minimum notice').fill('3');
    await page.getByRole('button', { name: 'Confirm settings' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Settings confirmed.');
    expect(stub.requests('put', '/api/v1/club/way-of-working').map((r) => r.body)).toEqual([
      { way_of_working: 'INSTANT' },
    ]);
    expect(stub.requests('put', '/api/v1/club/raketa-settings').map((r) => r.body)).toEqual([
      {
        release_lead_days: 3,
        cut_off_hours: 24,
        minimum_notice_hours: 3,
        time_to_confirm_minutes: 30,
        other_clubs_courts: { offered: false, within_km: 10 },
        paused: false,
      },
    ]);
    const way = stub.requests('put', '/api/v1/club/way-of-working')[0];
    const settings = stub.requests('put', '/api/v1/club/raketa-settings')[0];
    expect(way!.at).toBeLessThanOrEqual(settings!.at);
    expect(club.raketa.confirmed).toBe(true);
    await expect(page.getByRole('button', { name: 'Save settings' })).toBeVisible();

    await page.getByRole('navigation').getByRole('link', { name: 'Overview' }).click();
    const steps = page.getByRole('list', { name: 'Setup checklist' }).locator('[data-state]');
    await expect(steps).toHaveText(['not started', 'done ✓', 'to do', 'locked', 'done ✓']);
  });

  test('a confirmed club saves its settings, and keeping its way sends no way', async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.way = 'ONLY_RAKETA';
    club.raketa.confirmed = true;
    club.raketa.settings.release_lead_days = 5;
    await openSettings(page);

    await expect(page.getByRole('radio', { name: 'Only Raketa' })).toBeChecked();
    await expect(page.getByLabel('Release lead')).toHaveValue('5');
    await page.getByLabel('Free-cancellation cut-off').fill('12');
    await page.getByRole('button', { name: 'Save settings' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Settings saved.');
    expect(stub.requests('put', '/api/v1/club/way-of-working')).toEqual([]);
    expect(stub.requests('put', '/api/v1/club/raketa-settings')[0]?.body).toMatchObject({
      release_lead_days: 5,
      cut_off_hours: 12,
    });
  });

  test("other clubs' courts asks how far once it is on", async ({ page, stub, club }) => {
    club.raketa.way = 'INSTANT';
    await openSettings(page);
    await expect(page.getByLabel('Distance')).toHaveCount(0);

    await page
      .getByRole('switch', { name: "Offer our groups other clubs' courts when ours are full" })
      .check();
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
  });

  test('without a way chosen, nothing is sent and the way says why', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await openSettings(page);
    await page.getByRole('button', { name: 'Confirm settings' }).click();

    const ways = page.getByRole('radiogroup', { name: 'How you work with Raketa' });
    await expect(ways.getByText('Choose how you work with Raketa first.')).toBeVisible();
    expect(stub.requests('put', '/api/v1/club/way-of-working')).toEqual([]);
    expect(stub.requests('put', '/api/v1/club/raketa-settings')).toEqual([]);

    await ways.getByRole('radio', { name: 'Instant' }).check();
    await expect(ways.getByText('Choose how you work with Raketa first.')).toBeHidden();
  });

  test('a setting out of its range is refused under it, by this site or the server', async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.way = 'ONLY_RAKETA';
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
    club.raketa.way = 'INSTANT';
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
        minimum_notice_hours: 2,
        time_to_confirm_minutes: 30,
        other_clubs_courts: { offered: false, within_km: 10 },
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
    club.raketa.way = 'INSTANT';
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
    club.raketa.way = 'INSTANT';
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

  test('a way that landed stays chosen when the settings are refused, and is not sent again', async ({
    page,
    stub,
    club,
  }) => {
    stub.on('put', '/api/v1/club/raketa-settings', () => ({
      status: 400,
      body: refusal('setting_out_of_range', 'cut_off_hours', { least: 0, most: 72 }),
    }));
    await openSettings(page);
    await page.getByRole('radio', { name: 'Instant' }).check();
    await page.getByRole('button', { name: 'Confirm settings' }).click();
    await expect(page.getByText('A cut-off is 0 to 72 hours.')).toBeVisible();
    expect(club.raketa.way).toBe('INSTANT');

    // The backend takes the settings now: only they are sent, the way being recorded already.
    club.raketa.install();
    await page.getByLabel('Free-cancellation cut-off').fill('12');
    await page.getByRole('button', { name: 'Confirm settings' }).click();
    await expect(page.getByRole('main').getByRole('status')).toHaveText('Settings confirmed.');
    expect(stub.requests('put', '/api/v1/club/way-of-working')).toHaveLength(1);
  });

  test("the server's word that no way is chosen is said under the way", async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.way = 'INSTANT';
    stub.on('put', '/api/v1/club/raketa-settings', () => ({
      status: 409,
      body: refusal('way_of_working_not_chosen'),
    }));
    await openSettings(page);
    await page.getByRole('button', { name: 'Confirm settings' }).click();

    const ways = page.getByRole('radiogroup', { name: 'How you work with Raketa' });
    await expect(ways.getByText('Choose how you work with Raketa first.')).toBeVisible();
    await expect(page.getByRole('main').getByRole('status')).toHaveCount(0);
  });
});
