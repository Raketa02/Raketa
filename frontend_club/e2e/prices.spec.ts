import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { refusal } from './stub/backend';

/**
 * **Courts & prices: Prices** (#561, the screens B3, the mechanics §16.5): per sport the club
 * offers, a standard price per court-hour and optional price bands — weekdays or the weekend,
 * between two hours — each with the share it makes. One save replaces the whole table, and a
 * new price reaches new cards only, which the page says.
 */

async function openPrices(page: Page) {
  await signIn(page);
  await page.goto('/courts');
  return page.getByRole('region', { name: 'Prices' });
}

function sportRow(page: Page, sport: string) {
  return page.getByRole('region', { name: 'Prices' }).getByRole('group', { name: sport });
}

test.describe('Prices', () => {
  test('each sport the club offers is priced, with the share each player pays', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    const prices = await openPrices(page);
    await expect(prices).toContainText('New prices apply to new cards only');

    const padel = sportRow(page, 'Padel');
    const tennis = sportRow(page, 'Tennis');
    await expect(padel.getByLabel('Price per court-hour')).toHaveValue('');
    await expect(padel).toContainText('Not priced yet');
    await padel.getByLabel('Price per court-hour').fill('140');
    await expect(padel).toContainText('140 zł ÷ 4 = 35 zł each');
    await tennis.getByLabel('Price per court-hour').fill('90,50');
    await expect(tennis).toContainText('90,50 zł ÷ 2 = 45,25 zł each');
    await prices.getByRole('button', { name: 'Save prices' }).click();

    await expect(prices.getByRole('status')).toHaveText('Prices saved.');
    expect(stub.requests('put', '/api/v1/club/prices').map((r) => r.body)).toEqual([
      {
        prices: [
          { sport: 'PADEL', price_grosze: 140_00, bands: [] },
          { sport: 'TENNIS', price_grosze: 90_50, bands: [] },
        ],
      },
    ]);
    await page.reload();
    await expect(sportRow(page, 'Tennis').getByLabel('Price per court-hour')).toHaveValue('90,50');
  });

  test('a price band prices some hours differently', async ({ page, stub, club }) => {
    club.rakieta.price('PADEL', 120);
    const prices = await openPrices(page);
    const padel = sportRow(page, 'Padel');
    await expect(padel.getByLabel('Price per court-hour')).toHaveValue('120');

    await padel.getByRole('button', { name: '+ Add a price band' }).click();
    const band = padel.getByRole('group', { name: 'Price band 1' });
    await band.getByLabel('Days').selectOption('Weekdays');
    await band.getByLabel('From').selectOption('17:00');
    await band.getByLabel('Until').selectOption('22:00');
    await band.getByLabel('Price').fill('160');
    await expect(band).toContainText('160 zł ÷ 4 = 40 zł each');
    await prices.getByRole('button', { name: 'Save prices' }).click();

    await expect(prices.getByRole('status')).toHaveText('Prices saved.');
    expect(stub.requests('put', '/api/v1/club/prices')[0]?.body.prices).toEqual([
      {
        sport: 'PADEL',
        price_grosze: 120_00,
        bands: [{ days: 'WEEKDAYS', from_hour: 17, until_hour: 22, price_grosze: 160_00 }],
      },
    ]);

    // The band is the backend's now, and can be taken away again.
    await page.reload();
    const saved = sportRow(page, 'Padel').getByRole('group', { name: 'Price band 1' });
    await expect(saved.getByLabel('Price')).toHaveValue('160');
    await saved.getByRole('button', { name: 'Remove band' }).click();
    await expect(saved).toHaveCount(0);
    await page.getByRole('button', { name: 'Save prices' }).click();
    await expect(page.getByRole('region', { name: 'Prices' }).getByRole('status')).toHaveText(
      'Prices saved.',
    );
    expect(stub.requests('put', '/api/v1/club/prices')[1]?.body.prices[0]?.bands).toEqual([]);
  });

  test('what the site would refuse is said under its sport, and nothing is sent', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    const prices = await openPrices(page);
    const padel = sportRow(page, 'Padel');
    const tennis = sportRow(page, 'Tennis');

    await padel.getByLabel('Price per court-hour').fill('142,50');
    await tennis.getByLabel('Price per court-hour').fill('5');
    await prices.getByRole('button', { name: 'Save prices' }).click();
    await expect(
      padel.getByText('A padel price splits evenly among 4 players, to the grosz.'),
    ).toBeVisible();
    await expect(tennis.getByText('A court-hour costs 10 zł to 1000 zł.')).toBeVisible();

    await padel.getByLabel('Price per court-hour').fill('dużo');
    await tennis.getByLabel('Price per court-hour').fill('');
    await tennis.getByRole('button', { name: '+ Add a price band' }).click();
    await tennis.getByRole('group', { name: 'Price band 1' }).getByLabel('Price').fill('100');
    await prices.getByRole('button', { name: 'Save prices' }).click();
    await expect(padel.getByText('Type a price in złoty, like 120 or 142,50.')).toBeVisible();
    await expect(tennis.getByText('Price the court-hour before its bands.')).toBeVisible();
    expect(stub.requests('put', '/api/v1/club/prices')).toEqual([]);
  });

  test('bands that overlap, or hours that end before they start, are refused', async ({
    page,
    stub,
    club,
  }) => {
    club.rakieta.price('PADEL', 120);
    const prices = await openPrices(page);
    const padel = sportRow(page, 'Padel');
    await padel.getByRole('button', { name: '+ Add a price band' }).click();
    await padel.getByRole('button', { name: '+ Add a price band' }).click();
    const first = padel.getByRole('group', { name: 'Price band 1' });
    const second = padel.getByRole('group', { name: 'Price band 2' });
    for (const [band, from, until] of [
      [first, '17:00', '21:00'],
      [second, '20:00', '23:00'],
    ] as const) {
      await band.getByLabel('Days').selectOption('Weekdays');
      await band.getByLabel('From').selectOption(from);
      await band.getByLabel('Until').selectOption(until);
      await band.getByLabel('Price').fill('160');
    }
    await prices.getByRole('button', { name: 'Save prices' }).click();
    await expect(padel.getByText("Two bands of the same days can't overlap.")).toBeVisible();

    await second.getByLabel('Days').selectOption('Weekend');
    await second.getByLabel('From').selectOption('20:00');
    await second.getByLabel('Until').selectOption('20:00');
    await prices.getByRole('button', { name: 'Save prices' }).click();
    await expect(
      padel.getByText("A band's hours are within 07:00–23:00, ending after they start."),
    ).toBeVisible();
    expect(stub.requests('put', '/api/v1/club/prices')).toEqual([]);
  });

  test("the server's refusal lands under the sport it names", async ({ page, stub, club }) => {
    void club;
    stub.on('put', '/api/v1/club/prices', () => ({
      status: 400,
      body: refusal('price_out_of_range', 'prices', { sport: 'TENNIS', least: 1000, most: 100000 }),
    }));
    const prices = await openPrices(page);
    await sportRow(page, 'Tennis').getByLabel('Price per court-hour').fill('80');
    await prices.getByRole('button', { name: 'Save prices' }).click();

    await expect(
      sportRow(page, 'Tennis').getByText('A court-hour costs 10 zł to 1000 zł.'),
    ).toBeVisible();
    await expect(sportRow(page, 'Padel').getByText('A court-hour costs')).toHaveCount(0);
    await expect(prices.getByRole('status')).toHaveCount(0);
  });

  test('a sport the club stopped offering is said under its row', async ({ page, stub, club }) => {
    void club;
    stub.on('put', '/api/v1/club/prices', () => ({
      status: 400,
      body: refusal('price_sport_not_offered', 'prices', { sport: 'PADEL' }),
    }));
    const prices = await openPrices(page);
    await sportRow(page, 'Padel').getByLabel('Price per court-hour').fill('120');
    await prices.getByRole('button', { name: 'Save prices' }).click();

    await expect(
      sportRow(page, 'Padel').getByText(
        'Your club no longer offers padel. Tick it on Details first.',
      ),
    ).toBeVisible();
  });
});
