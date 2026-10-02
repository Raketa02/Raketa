import { expect, SESSION_COOKIE, signIn, test } from './fixtures';
import { refusal } from './stub/backend';
import { DESK_EMAIL, DESK_PASSWORD } from './stub/club';
import { SITE_PORT } from './suite';

test.describe('The cookie session', () => {
  test('is one sealed, httpOnly, SameSite=Lax cookie, and no token ever reaches the browser', async ({
    page,
    context,
    club,
  }) => {
    const seen: string[] = [];
    page.on('response', async (response) => {
      seen.push(JSON.stringify(await response.allHeaders()));
      const type = response.headers()['content-type'] ?? '';
      if (/html|text|json|javascript|x-component/.test(type)) {
        seen.push(await response.text().catch(() => ''));
      }
    });

    await signIn(page);
    await page.getByRole('button', { name: /Ogrody 33/ }).click();
    await page.getByRole('link', { name: 'Details' }).click();
    await expect(page.getByRole('heading', { name: 'Club details' })).toBeVisible();

    const cookies = await context.cookies();
    expect(cookies.map((cookie) => cookie.name)).toEqual([SESSION_COOKIE]);
    const [session] = cookies;
    expect(session).toMatchObject({ httpOnly: true, sameSite: 'Lax', path: '/', secure: false });
    expect(session?.value).not.toContain(club.accessToken(1));
    expect(session?.value).not.toContain(club.refreshToken(1));

    expect(await page.evaluate(() => document.cookie)).toBe('');
    const everything = seen.join('\n');
    expect(everything).not.toContain(club.accessToken(1));
    expect(everything).not.toContain(club.refreshToken(1));
  });

  test('survives a reload, without signing in again', async ({ page, stub, club }) => {
    void club;
    await signIn(page);
    await page.reload();

    await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
    await expect(page.getByRole('banner').getByText('Grzegórzki, Kraków')).toBeVisible();
    expect(stub.requests('post', '/api/v1/club/auth/login')).toHaveLength(1);
  });

  test('Sign out revokes the refresh token and returns to sign-in, and stays signed out', async ({
    page,
    context,
    stub,
    club,
  }) => {
    void club;
    await signIn(page);
    await page.getByRole('button', { name: 'Sign out' }).click();

    await expect(page).toHaveURL(/\/sign-in$/);
    await expect(page.getByLabel('Club email')).toBeVisible();
    expect(stub.requests('post', '/api/v1/club/auth/logout').map((r) => r.body)).toEqual([
      { refresh_token: club.refreshToken(1) },
    ]);
    expect(await context.cookies()).toEqual([]);

    await page.goto('/overview');
    await expect(page).toHaveURL(/\/sign-in$/);
  });

  test('a browser with no session is sent to sign-in from every signed-in page', async ({
    page,
    stub,
  }) => {
    for (const path of ['/', '/overview', '/groups', '/administrators', '/details']) {
      await page.goto(path);
      await expect(page, path).toHaveURL(/\/sign-in$/);
    }
    expect(stub.all()).toEqual([]);
  });

  test('the root opens Overview for a signed-in club', async ({ page, club }) => {
    void club;
    await signIn(page);
    await page.goto('/');
    await expect(page).toHaveURL(/\/overview$/);
  });

  test('an access token about to lapse is renewed before the page is drawn', async ({
    page,
    stub,
    club,
  }) => {
    club.shortLived();
    await signIn(page);

    await page.reload();
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
    // Renewed once, by whichever request first carried the lapsing pair.
    const [renewal, ...more] = stub.requests('post', '/api/v1/club/auth/refresh');
    expect(renewal?.body).toEqual({ refresh_token: club.refreshToken(1) });
    expect(more).toEqual([]);
    // Nothing read the club with the lapsing token once the renewal had begun.
    const reads = stub.requests('get', '/api/v1/club/details');
    const after = reads.filter((read) => read.at >= (renewal?.at ?? 0));
    expect(after.length).toBeGreaterThan(0);
    expect(
      after.every((read) => read.headers.authorization === `Bearer ${club.accessToken(2)}`),
    ).toBe(true);

    // The renewed pair is the one kept: the next page renews nothing.
    await page.reload();
    await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
    expect(stub.requests('post', '/api/v1/club/auth/refresh')).toHaveLength(1);
  });

  test('two pages at once renew the pair once: the refresh is single-flight', async ({
    page,
    context,
    stub,
    club,
  }) => {
    // A slow refresh, so every request that carries the lapsing pair is waiting on it together:
    // the two pages, and the links each one prefetches. A second presentation of refresh-1 would
    // be refused as spent, and would end the session.
    stub.on('post', '/api/v1/club/auth/refresh', async ({ body }) => {
      await new Promise((resolve) => setTimeout(resolve, 400));
      return body.refresh_token === club.refreshToken(1)
        ? { status: 200, body: club.issue() }
        : { status: 401, body: refusal('refresh_token_revoked') };
    });
    club.shortLived();
    await signIn(page);

    const other = await context.newPage();
    await Promise.all([page.goto('/details'), other.goto('/groups')]);

    await expect(page.getByRole('heading', { name: 'Club details' })).toBeVisible();
    await expect(other.getByRole('heading', { name: 'Groups' })).toBeVisible();
    await Promise.all([
      page.waitForLoadState('networkidle'),
      other.waitForLoadState('networkidle'),
    ]);
    expect(stub.requests('post', '/api/v1/club/auth/refresh').map((r) => r.body)).toEqual([
      { refresh_token: club.refreshToken(1) },
    ]);
    await other.reload();
    await expect(other.getByRole('heading', { name: 'Groups' })).toBeVisible();
  });

  test('a session the backend stopped accepting ends on sign-in, which says so', async ({
    page,
    context,
    club,
  }) => {
    await signIn(page);
    club.revokeAll();

    await page.goto('/details');
    await expect(page).toHaveURL(/\/sign-in\?session=ended$/);
    await expect(page.getByRole('main').getByRole('status')).toHaveText(
      "You've been signed out. Sign in again to carry on.",
    );
    expect(await context.cookies()).toEqual([]);
  });

  test('a page the backend refuses renews the pair and is drawn; if the renewal gets no answer, sign-in says so', async ({
    page,
    context,
    stub,
    club,
  }) => {
    await signIn(page);
    // Older than the five seconds under which a refused pair is not renewed again.
    await page.waitForTimeout(5_500);
    stub.on('get', '/api/v1/club/details', ({ headers }) =>
      headers.authorization === `Bearer ${club.accessToken(1)}`
        ? { status: 401, body: refusal('access_token_expired') }
        : { status: 200, body: club.details },
    );

    stub.on('post', '/api/v1/club/auth/refresh', () => ({ status: 'drop' }));
    await page.goto('/details');
    await expect(page).toHaveURL(/\/sign-in\?session=unreachable$/);
    await expect(page.getByRole('main').getByRole('status')).toHaveText(
      "We couldn't reach the server to keep you signed in. Try again in a moment.",
    );
    // Nothing was concluded from silence: the session is still there to renew.
    expect((await context.cookies()).map((cookie) => cookie.name)).toEqual([SESSION_COOKIE]);

    club.install();
    stub.on('get', '/api/v1/club/details', ({ headers }) =>
      headers.authorization === `Bearer ${club.accessToken(1)}`
        ? { status: 401, body: refusal('access_token_expired') }
        : { status: 200, body: club.details },
    );
    await page.goto('/details');
    await expect(page).toHaveURL(/\/details$/);
    await expect(page.getByLabel('Club name')).toHaveValue('Ogrody 33');
    expect(stub.requests('post', '/api/v1/club/auth/refresh').at(-1)?.body).toEqual({
      refresh_token: club.refreshToken(1),
    });
    expect(stub.requests('get', '/api/v1/club/details').at(-1)?.headers.authorization).toBe(
      `Bearer ${club.accessToken(2)}`,
    );
  });

  test('a page whose pair cannot be renewed ends the session and forgets the cookie', async ({
    page,
    context,
    club,
  }) => {
    await signIn(page);
    await page.waitForTimeout(5_500);
    club.revokeAll();

    await page.goto('/overview');
    await expect(page).toHaveURL(/\/sign-in\?session=ended$/);
    expect(await context.cookies()).toEqual([]);
    // With the cookie gone, the root goes straight to sign-in.
    await page.goto('/');
    await expect(page).toHaveURL(/\/sign-in$/);
  });

  test('a pair refused as soon as it is issued ends the session instead of going round', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    stub.on('get', '/api/v1/club/details', () => ({
      status: 401,
      body: refusal('access_token_invalid'),
    }));
    await page.goto('/sign-in');
    await page.getByLabel('Club email').fill(DESK_EMAIL);
    await page.getByLabel('Password').fill(DESK_PASSWORD);
    await page.getByRole('button', { name: 'Sign in' }).click();

    await expect(page).toHaveURL(/\/sign-in\?session=ended$/);
    expect(stub.requests('post', '/api/v1/club/auth/refresh')).toEqual([]);
  });

  test('a renewal only ever returns to a page of this site', async ({ page, club }) => {
    await signIn(page);
    void club;
    for (const to of [
      '//elsewhere.example/x',
      '/\\elsewhere.example',
      'https://elsewhere.example',
    ]) {
      await page.goto(`/session/renew?to=${encodeURIComponent(to)}`);
      await expect(page, to).toHaveURL(`http://127.0.0.1:${SITE_PORT}/overview`);
    }
  });

  test('a save the backend refuses with 401 renews the pair and is sent again', async ({
    page,
    stub,
    club,
  }) => {
    await signIn(page);
    await page.goto('/details');
    await expect(page.getByLabel('District')).toHaveValue('Grzegórzki');

    // The first token stops working though it has not lapsed; its refresh token still does.
    let refused = false;
    stub.on('put', '/api/v1/club/details', ({ headers, body }) => {
      if (headers.authorization === `Bearer ${club.accessToken(1)}`) {
        refused = true;
        return { status: 401, body: refusal('access_token_expired') };
      }
      club.details = { ...club.details, ...body };
      return { status: 200, body: club.details };
    });

    await page.getByLabel('District').fill('Grzegórzki Nowe');
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByRole('main').getByRole('status')).toHaveText('Club details saved.');
    expect(refused).toBe(true);
    expect(stub.requests('post', '/api/v1/club/auth/refresh').map((r) => r.body)).toEqual([
      { refresh_token: club.refreshToken(1) },
    ]);
    const saves = stub.requests('put', '/api/v1/club/details');
    expect(saves.map((r) => r.headers.authorization)).toEqual([
      `Bearer ${club.accessToken(1)}`,
      `Bearer ${club.accessToken(2)}`,
    ]);
    // The renewed pair was kept.
    await page.reload();
    await expect(page.getByLabel('District')).toHaveValue('Grzegórzki Nowe');
    expect(stub.requests('get', '/api/v1/club/details').at(-1)?.headers.authorization).toBe(
      `Bearer ${club.accessToken(2)}`,
    );
  });

  test('a save whose pair cannot be renewed ends the session', async ({ page, club }) => {
    await signIn(page);
    await page.goto('/details');
    await expect(page.getByLabel('City')).toHaveValue('Kraków');
    club.revokeAll();

    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page).toHaveURL(/\/sign-in\?session=ended$/);
  });
});
