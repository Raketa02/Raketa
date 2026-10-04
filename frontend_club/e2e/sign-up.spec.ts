import { expect, mapReady, test } from './fixtures';
import { refusal } from './stub/backend';
import { MAP_START } from './suite';

const NEW_CLUB = {
  name: 'Ogrody 33',
  district: 'Grzegórzki',
  city: 'Kraków',
  email: 'desk@ogrody33.pl',
  password: 'kort33ogrody',
};

test.describe('Sign up', () => {
  test('the desk signs Ogrody 33 up with a pin on the map, and is signed straight in', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await page.goto('/sign-in');
    await page.getByRole('link', { name: 'Sign up' }).click();
    await expect(page.getByRole('heading', { name: 'Sign up your club' })).toBeVisible();

    await page.getByLabel('Club name').fill(NEW_CLUB.name);
    await page.getByLabel('District').fill(NEW_CLUB.district);
    await page.getByLabel('City').fill(NEW_CLUB.city);
    // Ticked in the story's order; the request lists them in the registry's.
    await page.getByRole('checkbox', { name: 'Tennis' }).check();
    await page.getByRole('checkbox', { name: 'Padel' }).check();
    const map = await mapReady(page);
    await expect(page.getByText('No pin yet.')).toBeVisible();
    await map.click(); // the middle of the map, which opens on MAP_START
    await expect(page.getByText(/^Pin at 50\.061\d\d, 19\.936\d\d$/)).toBeVisible();
    await page.getByLabel('Club email').fill(NEW_CLUB.email);
    await page.getByLabel('Password').fill(NEW_CLUB.password);
    await page.getByRole('button', { name: 'Sign up' }).click();

    await expect(page).toHaveURL(/\/overview$/);
    await expect(page.getByRole('banner').getByRole('link', { name: /Ogrody 33/ })).toHaveText(
      'Ogrody 33 · Grzegórzki, Kraków',
    );

    const [signUp] = stub.requests('post', '/api/v1/club/sign-up');
    expect(signUp?.body).toMatchObject({
      name: NEW_CLUB.name,
      district: NEW_CLUB.district,
      city: NEW_CLUB.city,
      sports: ['PADEL', 'TENNIS'],
      email: NEW_CLUB.email,
      password: NEW_CLUB.password,
    });
    expect(signUp?.body.point.latitude).toBeCloseTo(MAP_START.latitude, 3);
    expect(signUp?.body.point.longitude).toBeCloseTo(MAP_START.longitude, 3);
    expect(stub.requests('post', '/api/v1/club/auth/login').map((r) => r.body)).toEqual([
      { email: NEW_CLUB.email, password: NEW_CLUB.password },
    ]);
  });

  test('the map draws OpenStreetMap tiles from the configured URL, with attribution', async ({
    page,
    stub,
  }) => {
    await page.goto('/sign-up');
    await mapReady(page);

    await expect.poll(() => stub.tiles).toBeGreaterThan(0);
    const credit = page.getByRole('link', { name: 'OpenStreetMap' });
    await expect(credit).toHaveAttribute('href', 'https://www.openstreetmap.org/copyright');
    await expect(page.getByText('contributors')).toBeVisible();
  });

  test('the pin can be put in the middle of the map without a pointer', async ({ page }) => {
    await page.goto('/sign-up');
    await mapReady(page);
    await page.getByRole('button', { name: 'Put the pin in the middle of the map' }).click();
    await expect(page.getByText('Pin at 50.06140, 19.93660')).toBeVisible();
  });

  test('every field it refuses says why under that field, and nothing is sent', async ({
    page,
    stub,
  }) => {
    await page.goto('/sign-up');
    await page.getByLabel('Club name').fill('O');
    await page.getByLabel('Club email').fill('desk@');
    await page.getByLabel('Password').fill('lettersonly');
    await page.getByRole('button', { name: 'Sign up' }).click();

    await expect(page.getByText('A club name is 2 to 80 characters.')).toBeVisible();
    await expect(page.getByText('A district is 2 to 64 characters.')).toBeVisible();
    await expect(page.getByText('A city is 2 to 64 characters.')).toBeVisible();
    await expect(page.getByText('Pick at least one sport the club offers.')).toBeVisible();
    await expect(page.getByText('Drop a pin on the map where the club is.')).toBeVisible();
    await expect(page.getByText("That doesn't look like an email address.")).toBeVisible();
    await expect(page.getByLabel('Password')).toHaveAttribute('aria-invalid', 'true');
    // What was typed stays typed.
    await expect(page.getByLabel('Club name')).toHaveValue('O');
    expect(stub.requests('post', '/api/v1/club/sign-up')).toEqual([]);
  });

  async function fillValidly(page: import('@playwright/test').Page) {
    await page.getByLabel('Club name').fill(NEW_CLUB.name);
    await page.getByLabel('District').fill(NEW_CLUB.district);
    await page.getByLabel('City').fill(NEW_CLUB.city);
    await page.getByRole('checkbox', { name: 'Padel' }).check();
    await (await mapReady(page)).click();
    await page.getByLabel('Club email').fill(NEW_CLUB.email);
    await page.getByLabel('Password').fill(NEW_CLUB.password);
  }

  test("another club's email is refused under the email box, and the rest stays typed", async ({
    page,
    stub,
  }) => {
    stub.on('post', '/api/v1/club/sign-up', () => ({
      status: 409,
      body: refusal('club_email_already_registered', 'email'),
    }));
    await page.goto('/sign-up');
    await fillValidly(page);
    await page.getByRole('button', { name: 'Sign up' }).click();

    await expect(page.getByText('Another club already signs in with this email.')).toBeVisible();
    await expect(page.getByLabel('Club email')).toHaveAttribute('aria-invalid', 'true');
    await expect(page.getByLabel('Password')).toHaveValue(NEW_CLUB.password);
    await expect(page.getByRole('checkbox', { name: 'Padel' })).toBeChecked();
    await expect(page).toHaveURL(/\/sign-up$/);
    expect(stub.requests('post', '/api/v1/club/auth/login')).toEqual([]);
  });

  test('a club whose first sign-in fails is told it is signed up, on sign-in', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    await page.goto('/sign-up');
    await fillValidly(page);
    stub.on('post', '/api/v1/club/auth/login', () => ({ status: 'drop' }));
    await page.getByRole('button', { name: 'Sign up' }).click();

    await expect(page).toHaveURL(/\/sign-in\?signed-up=1$/);
    await expect(page.getByRole('main').getByRole('status')).toHaveText(
      'Your club is signed up. Sign in with its email and password.',
    );
    expect(stub.requests('post', '/api/v1/club/sign-up')).toHaveLength(1);
  });

  test('a refusal the backend names a field for lands under that field', async ({ page, stub }) => {
    stub.on('post', '/api/v1/club/sign-up', () => ({
      status: 400,
      body: refusal('club_point_invalid', 'point'),
    }));
    await page.goto('/sign-up');
    await fillValidly(page);
    await page.getByRole('button', { name: 'Sign up' }).click();

    await expect(
      page.getByText("That pin isn't on the map. Drop it again where the club is."),
    ).toBeVisible();
  });
});
