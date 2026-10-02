import { expect, mapReady, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { OGRODY_33 } from './stub/club';
import { court } from './stub/courts';

test.describe('Club details', () => {
  test("opens from the club's menu in the top bar, holding every sign-up detail", async ({
    page,
    club,
  }) => {
    void club;
    await signIn(page);
    const bar = page.getByRole('banner');
    await bar.getByRole('button', { name: /Ogrody 33/ }).click();
    await bar.getByRole('link', { name: 'Details' }).click();

    await expect(page).toHaveURL(/\/details$/);
    await expect(page.getByRole('heading', { name: 'Club details' })).toBeVisible();
    await expect(page.getByLabel('Club name')).toHaveValue('Ogrody 33');
    await expect(page.getByLabel('District')).toHaveValue('Grzegórzki');
    await expect(page.getByLabel('City')).toHaveValue('Kraków');
    await expect(page.getByRole('checkbox', { name: 'Padel' })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: 'Tennis' })).toBeChecked();
    await expect(page.getByRole('checkbox', { name: 'Squash' })).not.toBeChecked();
    await expect(page.getByRole('checkbox', { name: 'Badminton' })).not.toBeChecked();
    await mapReady(page);
    await expect(page.getByText('Pin at 50.05920, 19.95750')).toBeVisible();
  });

  test('the desk moves the pin two streets over and saves it', async ({ page, stub, club }) => {
    void club;
    await signIn(page);
    await page.goto('/details');
    const map = await mapReady(page);

    // A click right of the middle: the map opens centred on the pin.
    const box = await map.boundingBox();
    if (box === null) throw new Error('the map has no box');
    await map.click({ position: { x: box.width / 2 + 60, y: box.height / 2 } });
    await expect(page.getByText('Pin at 50.05920, 19.95750')).toBeHidden();
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Club details saved.');
    const [save] = stub.requests('put', '/api/v1/club/details');
    expect(save?.body).toMatchObject({
      name: 'Ogrody 33',
      district: 'Grzegórzki',
      city: 'Kraków',
      sports: ['PADEL', 'TENNIS'],
    });
    expect(save?.body.point.latitude).toBeCloseTo(OGRODY_33.point.latitude, 4);
    expect(save?.body.point.longitude).toBeGreaterThan(OGRODY_33.point.longitude);

    await page.reload();
    await mapReady(page);
    await expect(page.getByText('Pin at 50.05920, 19.95750')).toBeHidden();
  });

  test('a rename is saved as the backend records it, and the top bar says it at once', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await signIn(page);
    await page.goto('/details');
    await page.getByLabel('Club name').fill('  Ogrody   33 Club ');
    await page.getByRole('checkbox', { name: 'Squash' }).check();
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Club details saved.');
    await expect(page.getByLabel('Club name')).toHaveValue('Ogrody 33 Club');
    await expect(
      page.getByRole('banner').getByRole('button', { name: /Ogrody 33 Club/ }),
    ).toHaveText('Ogrody 33 Club · Grzegórzki, Kraków');
    expect(stub.requests('put', '/api/v1/club/details')[0]?.body.sports).toEqual([
      'PADEL',
      'TENNIS',
      'SQUASH',
    ]);
  });

  test('a detail it refuses is said under its field, and nothing is sent', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await signIn(page);
    await page.goto('/details');
    await page.getByLabel('City').fill('K');
    await page.getByRole('checkbox', { name: 'Padel' }).uncheck();
    await page.getByRole('checkbox', { name: 'Tennis' }).uncheck();
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('A city is 2 to 64 characters.')).toBeVisible();
    await expect(page.getByText('Pick at least one sport the club offers.')).toBeVisible();
    expect(stub.requests('put', '/api/v1/club/details')).toEqual([]);
  });

  test("the server's refusal is shown under the field it names", async ({ page, stub, club }) => {
    void club;
    stub.on('put', '/api/v1/club/details', () => ({
      status: 400,
      body: refusal('club_district_invalid', 'district'),
    }));
    await signIn(page);
    await page.goto('/details');
    await page.getByLabel('District').fill('Grzegórzki');
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('A district is 2 to 64 characters.')).toBeVisible();
    await expect(page.getByLabel('District')).toHaveAttribute('aria-invalid', 'true');
    await expect(page.getByRole('main').getByRole('status')).toHaveCount(0);
  });

  test('unticking a sport an official group plays is refused, naming the group', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    stub.on('put', '/api/v1/club/details', () => ({
      status: 409,
      body: refusal('club_sport_declared_by_group', 'sports', {
        sport: 'PADEL',
        group: 'Ogrody 33 Club',
      }),
    }));
    await signIn(page);
    await page.goto('/details');
    const padel = page.getByRole('checkbox', { name: 'Padel' });
    await padel.uncheck();
    await page.getByRole('button', { name: 'Save' }).click();

    const sports = page.getByRole('group', { name: 'Sports offered' });
    await expect(
      sports.getByText('Ogrody 33 Club plays padel. Tick padel again to save the rest.'),
    ).toBeVisible();
    await expect(sports).toHaveAttribute('aria-invalid', 'true');
    await expect(page.getByRole('main').getByRole('status')).toHaveCount(0);

    // Ticking it again is the other way out, and takes the refusal with it.
    await padel.check();
    await expect(sports.getByText(/plays padel/)).toBeHidden();
  });

  test('unticking a sport one of its courts plays is refused, naming the court', async ({
    page,
    stub,
    club,
  }) => {
    club.raketa.courts = [court({ name: 'Kort centralny', sport: 'TENNIS', offered: false })];
    await signIn(page);
    await page.goto('/details');
    await page.getByRole('checkbox', { name: 'Tennis' }).uncheck();
    await page.getByRole('button', { name: 'Save' }).click();

    const sports = page.getByRole('group', { name: 'Sports offered' });
    await expect(
      sports.getByText('Kort centralny is a tennis court. Tick tennis again to save the rest.'),
    ).toBeVisible();
    await expect(sports).toHaveAttribute('aria-invalid', 'true');
    expect(stub.requests('put', '/api/v1/club/details')).toHaveLength(1);
    expect(club.details.sports).toEqual(['PADEL', 'TENNIS']);
  });

  test('a refusal this site has no sentence for still lands under the field it names', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    stub.on('put', '/api/v1/club/details', () => ({
      status: 400,
      body: refusal('some_new_refusal', 'sports'),
    }));
    await signIn(page);
    await page.goto('/details');
    await page.getByRole('button', { name: 'Save' }).click();

    const sports = page.getByRole('group', { name: 'Sports offered' });
    await expect(sports.getByText('Something went wrong. Try again.')).toBeVisible();
  });
});
