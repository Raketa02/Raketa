import { expect, mapReady, signIn, test } from './fixtures';
import type { GeocodedPlace } from './stub/backend';
import { OGRODY_33 } from './stub/club';
import { MAP_START } from './suite';

/**
 * **Finding the club by its address**: the desk types the address over the map, presses Enter or
 * _Find_, and the map and the pin go there — the server asks the geocoder (Nominatim, through
 * `GEOCODER_URL`), and the best match wins. The found place's name is said under the box so the
 * desk can check it, and the pin can still be dragged.
 */

/** Warsaw: far enough from the map's opening view that the pin is only on screen if the map went. */
const PLAC_DEFILAD: GeocodedPlace = {
  lat: '52.2316',
  lon: '21.0059',
  display_name: 'Plac Defilad 1, Śródmieście, Warszawa, Polska',
};

const FLORIANSKA: GeocodedPlace = {
  lat: '50.0633',
  lon: '19.9393',
  display_name: 'Floriańska 3, Stare Miasto, Kraków, Polska',
};

const box = (page: import('@playwright/test').Page) => page.getByLabel('Address');

test.describe('Finding the club by its address', () => {
  test('Enter takes the map and the pin to the address, says what it found, and signs nobody up', async ({
    page,
    stub,
  }) => {
    stub.places = [PLAC_DEFILAD];
    await page.goto('/sign-up');
    const map = await mapReady(page);

    await box(page).fill('Plac Defilad 1, Warszawa');
    await box(page).press('Enter');

    await expect(page.getByText('Pin at 52.23160, 21.00590')).toBeVisible();
    await expect(
      page.getByText('Found: Plac Defilad 1, Śródmieście, Warszawa, Polska'),
    ).toBeVisible();

    // The map went there too: at Kraków's opening view, Warsaw is off the map.
    const pin = await map.locator('.leaflet-marker-icon').boundingBox();
    const frame = await map.boundingBox();
    if (pin === null || frame === null) throw new Error('the pin or the map has no box');
    expect(pin.x).toBeGreaterThanOrEqual(frame.x);
    expect(pin.y).toBeGreaterThanOrEqual(frame.y);
    expect(pin.x + pin.width).toBeLessThanOrEqual(frame.x + frame.width);
    expect(pin.y + pin.height).toBeLessThanOrEqual(frame.y + frame.height);

    // Enter searched: the sign-up form was not sent.
    expect(stub.requests('post', '/api/v1/club/sign-up')).toEqual([]);
    expect(stub.searches).toHaveLength(1);
  });

  test('the server asks for the one best match, near the map, saying who it is', async ({
    page,
    stub,
  }) => {
    stub.places = [FLORIANSKA];
    await page.goto('/sign-up');
    await mapReady(page);

    await box(page).fill('  Floriańska 3  ');
    await page.getByRole('button', { name: 'Find' }).click();
    await expect(page.getByText('Pin at 50.06330, 19.93930')).toBeVisible();

    const [search] = stub.searches;
    expect(search?.query.get('q')).toBe('Floriańska 3');
    expect(search?.query.get('format')).toBe('jsonv2');
    expect(search?.query.get('limit')).toBe('1');
    // Biased towards where the map opens, not bounded to it: a club elsewhere is still found.
    const [west, north, east, south] = (search?.query.get('viewbox') ?? '').split(',').map(Number);
    expect(west).toBeLessThan(MAP_START.longitude);
    expect(east).toBeGreaterThan(MAP_START.longitude);
    expect(south).toBeLessThan(MAP_START.latitude);
    expect(north).toBeGreaterThan(MAP_START.latitude);
    expect(search?.query.get('bounded')).toBe('0');
    // Nominatim's usage policy asks every caller to identify itself.
    expect(search?.agent).toMatch(/^Raketa for Clubs/);
  });

  test('an address it cannot find is said under the box, and the pin stays where it was', async ({
    page,
    stub,
  }) => {
    await page.goto('/sign-up');
    await mapReady(page);

    await box(page).fill('Nowhere Street 999');
    await box(page).press('Enter');

    await expect(
      page.getByText('Nothing found for that address. Try adding the city.'),
    ).toBeVisible();
    await expect(page.getByText('No pin yet.')).toBeVisible();
    expect(stub.searches).toHaveLength(1);
  });

  test('a geocoder that is down is said, and the map still takes a pin', async ({ page, stub }) => {
    stub.geocoderStatus = 503;
    await page.goto('/sign-up');
    const map = await mapReady(page);

    await box(page).fill('Floriańska 3, Kraków');
    await box(page).press('Enter');

    await expect(
      page.getByText("The address search isn't answering. Drop the pin on the map instead."),
    ).toBeVisible();
    await map.click();
    await expect(page.getByText('No pin yet.')).toBeHidden();
  });

  test('two letters are not an address, and nothing is asked', async ({ page, stub }) => {
    await page.goto('/sign-up');
    await mapReady(page);

    await box(page).fill('Fl');
    await box(page).press('Enter');

    await expect(page.getByText('Type at least 3 characters of the address.')).toBeVisible();
    expect(stub.searches).toEqual([]);
  });

  test('Club details finds the address too, and saves the pin it put there', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    stub.places = [FLORIANSKA];
    await signIn(page);
    await page.goto('/details');
    await mapReady(page);

    await box(page).fill('Floriańska 3, Kraków');
    await box(page).press('Enter');
    await expect(page.getByText('Pin at 50.06330, 19.93930')).toBeVisible();
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Club details saved.');
    const [save] = stub.requests('put', '/api/v1/club/details');
    expect(save?.body.point).toEqual({ latitude: 50.0633, longitude: 19.9393 });
    expect(save?.body.name).toBe(OGRODY_33.name);
  });
});
