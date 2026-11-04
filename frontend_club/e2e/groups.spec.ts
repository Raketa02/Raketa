import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { administrator, DAY_MS, fromNow, joinRequest, officialGroup } from './stub/club';

/**
 * **The Groups page, a group's page and the handover** (#524, club mocks 15–16 and 20): the club
 * watches its official groups fill up from the groups they mirror, answers who asks to join
 * (ADR-0191 §1), and moves each one between its administrators.
 */

/** An administrator who took up the invitation and used the profile this week. */
function active(name: string, email: string) {
  return administrator({
    name,
    email,
    status: 'ACTIVE',
    last_used_at: fromNow(-3 * DAY_MS),
    expires_at: null,
  });
}

async function openGroups(page: Page) {
  await signIn(page);
  await page.getByRole('navigation').getByRole('link', { name: 'Groups' }).click();
  await expect(page.getByRole('heading', { name: 'Groups', exact: true })).toBeVisible();
}

/** The row a group's name heads. */
function rowOf(page: Page, name: string) {
  return page.getByRole('row').filter({ has: page.getByRole('rowheader', { name, exact: true }) });
}

/**
 * The colour on screen `across` the way along a row's bar (0 its left end, 1 its right), read
 * from a picture of it: what the desk sees, which no style property says for a progress bar.
 */
async function barColourAt(page: Page, name: string, across: number) {
  const picture = await rowOf(page, name).locator('progress').screenshot();
  return page.evaluate(
    async ({ png, across }) => {
      const image = new Image();
      image.src = `data:image/png;base64,${png}`;
      await image.decode();
      const canvas = document.createElement('canvas');
      canvas.width = image.width;
      canvas.height = image.height;
      const context = canvas.getContext('2d');
      if (context === null) throw new Error('no 2d canvas');
      context.drawImage(image, 0, 0);
      const x = Math.floor((image.width - 1) * across);
      const [red, green, blue] = context.getImageData(x, Math.floor(image.height / 2), 1, 1).data;
      return `rgb(${red}, ${green}, ${blue})`;
    },
    { png: picture.toString('base64'), across },
  );
}

const GREEN = 'rgb(48, 131, 97)';
const TRACK = 'rgb(238, 236, 227)';

test.describe('Groups', () => {
  test("the table reads each group's administrator, players and crowd, and nothing is created here", async ({
    page,
    club,
  }) => {
    const marta = active('Marta Wójcik', 'marta@ogrody33.pl');
    club.administrators = [marta];
    club.groups = [
      officialGroup({
        name: 'Ogrody open play',
        runBy: marta,
        member_count: 8,
        whatsapp_size: 30,
        whatsapp_percent: 27,
      }),
      officialGroup({
        name: 'Ogrody 33 Club',
        runBy: marta,
        member_count: 11,
        waiting_count: 1,
        whatsapp_size: 48,
        whatsapp_percent: 23,
        games: 0,
      }),
    ];
    await openGroups(page);

    await expect(page.getByText('Official groups at Ogrody 33')).toBeVisible();
    await expect(page.getByText('Created by your administrators in the app')).toBeVisible();
    await expect(page.getByRole('main').getByRole('button')).toHaveCount(0);

    const table = page.getByRole('table');
    await expect(table.getByRole('columnheader')).toHaveText([
      'Group',
      'Administrator',
      'Players',
      'From original group',
      'Games',
    ]);
    await expect(table.getByRole('rowheader')).toHaveText(['Ogrody 33 Club', 'Ogrody open play']);
    const club33 = rowOf(page, 'Ogrody 33 Club');
    await expect(club33.getByRole('cell')).toHaveText([
      'Marta Wójcik',
      /^11\s*1 waiting$/,
      '11 of 48 · 23%',
      '0',
    ]);
    await expect(rowOf(page, 'Ogrody open play').getByRole('cell')).toHaveText([
      'Marta Wójcik',
      '8',
      '8 of 30 · 27%',
      '0',
    ]);
    await expect(club33.getByText('1 waiting')).toHaveCSS('color', 'rgb(135, 100, 26)');
  });

  test('Games counts the games booked in each group', async ({ page, club }) => {
    club.groups = [
      officialGroup({ name: 'Ogrody 33 Club', member_count: 11, games: 7 }),
      officialGroup({ name: 'Ogrody open play', member_count: 8 }),
    ];
    await openGroups(page);
    await expect(rowOf(page, 'Ogrody 33 Club').getByRole('cell').last()).toHaveText('7');
    await expect(rowOf(page, 'Ogrody open play').getByRole('cell').last()).toHaveText('0');
  });

  test("a line over the table says whether the groups are offered other clubs' courts, and leads to the setting", async ({
    page,
    club,
  }) => {
    club.groups = [officialGroup({ name: 'Ogrody 33 Club', member_count: 11 })];
    await openGroups(page);

    const line = page.getByRole('main').getByText(/^When your courts are full/);
    await expect(line).toHaveText(
      "When your courts are full, your groups are offered only yours. Offer other clubs' courts in Raketa settings.",
    );
    await line.getByRole('link', { name: 'Raketa settings' }).click();
    await expect(page).toHaveURL(/\/raketa-settings#other-clubs$/);
    await expect(
      page.getByRole('switch', { name: "Offer our groups other clubs' courts when ours are full" }),
    ).toBeInViewport();

    club.raketa.settings.other_clubs_courts = { offered: true, within_km: 15 };
    await page.goto('/groups');
    await expect(page.getByRole('main').getByText(/^When your courts are full/)).toHaveText(
      "When your courts are full, your groups are also offered other clubs' courts within 15 km. Change it in Raketa settings.",
    );
  });

  test('with no official groups, there is no line about other clubs', async ({ page, club }) => {
    void club;
    await openGroups(page);
    await expect(page.getByText(/^When your courts are full/)).toHaveCount(0);
  });

  test('From original group is drawn as a bar, full with the real figure past 100%', async ({
    page,
    club,
  }) => {
    const marta = active('Marta Wójcik', 'marta@ogrody33.pl');
    club.administrators = [marta];
    club.groups = [
      officialGroup({ name: 'Ogrody 33 Club', runBy: marta, member_count: 12, whatsapp_size: 48 }),
      officialGroup({
        name: 'Ogrody wieczorem',
        runBy: marta,
        member_count: 52,
        whatsapp_size: 48,
      }),
    ];
    await openGroups(page);

    /** How much of its track a row's bar fills, as drawn. */
    const filled = (name: string) =>
      rowOf(page, name)
        .getByRole('cell')
        .nth(2)
        .locator('progress')
        .evaluate((bar: HTMLProgressElement) => bar.position);

    await expect(rowOf(page, 'Ogrody wieczorem').getByRole('cell').nth(2)).toHaveText(
      '52 of 48 · 108%',
    );
    expect(await filled('Ogrody wieczorem')).toBe(1);
    await expect(rowOf(page, 'Ogrody 33 Club').getByRole('cell').nth(2)).toHaveText(
      '12 of 48 · 25%',
    );
    expect(await filled('Ogrody 33 Club')).toBe(0.25);

    // Green as far as the players reach, then the pale track; green to the end past 100%.
    expect(await barColourAt(page, 'Ogrody 33 Club', 0.1)).toBe(GREEN);
    expect(await barColourAt(page, 'Ogrody 33 Club', 0.9)).toBe(TRACK);
    expect(await barColourAt(page, 'Ogrody wieczorem', 0.9)).toBe(GREEN);
  });

  test('a group whose administrator was removed needs an administrator, in amber', async ({
    page,
    club,
  }) => {
    const marta = active('Marta Wójcik', 'marta@ogrody33.pl');
    club.administrators = [marta];
    club.groups = [officialGroup({ name: 'Ogrody 33 Club', runBy: marta, member_count: 11 })];
    await signIn(page);
    await page.goto('/administrators');
    await page.getByRole('button', { name: 'Remove' }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Remove' }).click();
    await expect(page.getByRole('rowheader', { name: 'Marta Wójcik' })).toHaveCount(0);

    await page.getByRole('navigation').getByRole('link', { name: 'Groups' }).click();
    const administrator = rowOf(page, 'Ogrody 33 Club').getByRole('cell').first();
    await expect(administrator).toHaveText('needs an administrator');
    await expect(administrator.getByText('needs an administrator')).toHaveCSS(
      'color',
      'rgb(135, 100, 26)',
    );
  });
});

test.describe('Groups, before there are any', () => {
  test('says where official groups come from, in place of an empty table', async ({
    page,
    club,
  }) => {
    void club;
    await openGroups(page);
    await expect(page.getByRole('table')).toHaveCount(0);
    await expect(page.getByRole('main')).toContainText(
      'No official groups yet. Your administrators create them in the Raketa app.',
    );
    await expect(page.getByRole('main').getByRole('button')).toHaveCount(0);
  });
});

test.describe('Hand over', () => {
  test('the desk taps a group that needs an administrator and hands it to Tomek, once sure', async ({
    page,
    stub,
    club,
  }) => {
    const tomek = active('Tomek K.', 'tomek.k@gmail.com');
    const ola = administrator({ name: 'Ola Nowak', email: 'ola@ogrody33.pl' });
    const group = officialGroup({
      name: 'Ogrody 33 Club',
      member_count: 11,
      waiting_count: 1,
      whatsapp_size: 48,
    });
    club.administrators = [ola, tomek];
    club.groups = [group];
    await openGroups(page);

    // Anywhere on the row opens it, not only the name: here, its far end, past Games.
    const row = rowOf(page, 'Ogrody 33 Club');
    const box = await row.boundingBox();
    if (box === null) throw new Error('the row has no box');
    await row.click({ position: { x: box.width - 4, y: box.height / 2 } });
    await expect(page).toHaveURL(new RegExp(`/groups/${group.id}$`));
    await expect(page.getByRole('heading', { name: 'Ogrody 33 Club' })).toBeVisible();
    await expect(page.getByText('Official group', { exact: true })).toBeVisible();
    await expect(page.getByText('needs an administrator')).toHaveCSS('color', 'rgb(135, 100, 26)');
    await expect(page.getByRole('main')).toContainText(
      'Its link, who can join and its group size stay as they are.',
    );
    await expect(page.getByRole('main')).not.toContainText('WhatsApp');

    // Ola hasn't taken up her invitation, so only Tomek can take it.
    const choices = page.getByRole('group', { name: 'Hand it over to' });
    await expect(choices.getByRole('radio')).toHaveCount(1);
    const handOver = page.getByRole('button', { name: 'Hand over', exact: true });
    await expect(handOver).toBeDisabled();
    await choices.getByRole('radio', { name: /Tomek K\./ }).check();

    const dialog = page.getByRole('dialog', { name: 'Hand Ogrody 33 Club over to Tomek K.?' });
    await handOver.click();
    await expect(dialog).toContainText('Tomek K. answers its join requests from now on');
    await expect(dialog).toContainText('Raketa tells Tomek K. in the app.');
    await dialog.getByRole('button', { name: 'Cancel' }).click();
    await expect(dialog).toBeHidden();
    expect(stub.requests('put', '/api/v1/club/groups/{group_id}/administrator')).toEqual([]);

    await handOver.click();
    await dialog.getByRole('button', { name: 'Hand over' }).click();

    await expect(page).toHaveURL(/\/groups$/);
    await expect(rowOf(page, 'Ogrody 33 Club').getByRole('cell').first()).toHaveText('Tomek K.');
    expect(
      stub
        .requests('put', '/api/v1/club/groups/{group_id}/administrator')
        .map((request) => ({ group: request.params.group_id, body: request.body })),
    ).toEqual([{ group: group.id, body: { administrator_id: tomek.id } }]);
  });

  test('a keyboard choosing somebody and pressing Enter is asked first too', async ({
    page,
    stub,
    club,
  }) => {
    club.administrators = [active('Tomek K.', 'tomek.k@gmail.com')];
    const group = officialGroup({ name: 'Ogrody 33 Club' });
    club.groups = [group];
    await signIn(page);
    await page.goto(`/groups/${group.id}`);
    const tomek = page.getByRole('radio', { name: /Tomek K\./ });
    await tomek.focus();
    await page.keyboard.press('Space');
    await expect(tomek).toBeChecked();
    await page.keyboard.press('Enter');

    // Enter on a radio submits its form implicitly, and nothing may go without the question.
    await expect(page.getByRole('button', { name: 'Hand over', exact: true })).toBeEnabled();
    await page.waitForTimeout(500);
    expect(stub.requests('put', '/api/v1/club/groups/{group_id}/administrator')).toEqual([]);
    await expect(page).toHaveURL(new RegExp(`/groups/${group.id}$`));
  });

  test('a group somebody runs names them, and is offered to everyone else who is active', async ({
    page,
    club,
  }) => {
    const marta = active('Marta Wójcik', 'marta@ogrody33.pl');
    const tomek = active('Tomek K.', 'tomek.k@gmail.com');
    const bartek = active('Bartek Zieliński', 'bartek@ogrody33.pl');
    club.administrators = [bartek, marta, tomek];
    const group = officialGroup({ name: 'Ogrody open play', runBy: marta });
    club.groups = [group];
    await signIn(page);
    await page.goto(`/groups/${group.id}`);

    await expect(page.getByRole('heading', { name: 'Ogrody open play' })).toBeVisible();
    await expect(page.getByRole('main')).toContainText(/Administrator\s*Marta Wójcik/);
    const choices = page.getByRole('group', { name: 'Hand it over to' });
    await expect(choices.getByRole('radio')).toHaveCount(2);
    await expect(choices.getByRole('listitem')).toHaveText([
      /Bartek Zieliński\s*bartek@ogrody33\.pl/,
      /Tomek K\.\s*tomek\.k@gmail\.com/,
    ]);

    await choices.getByRole('radio', { name: /Bartek/ }).check();
    await page.getByRole('button', { name: 'Hand over', exact: true }).click();
    await expect(
      page.getByRole('dialog', { name: 'Hand Ogrody open play over to Bartek Zieliński?' }),
    ).toContainText(
      'Bartek Zieliński answers its join requests from now on, and Marta Wójcik stops seeing it ' +
        'in the app.',
    );

    await page.keyboard.press('Escape');
    await page.getByRole('link', { name: 'Cancel' }).click();
    await expect(page).toHaveURL(/\/groups$/);
  });

  test('with nobody to hand it to, the page says to invite an administrator first', async ({
    page,
    club,
  }) => {
    const marta = active('Marta Wójcik', 'marta@ogrody33.pl');
    club.administrators = [
      administrator({ name: 'Ola Nowak', email: 'ola@ogrody33.pl' }),
      administrator({ name: 'Ewa Lis', email: 'ewa@ogrody33.pl', status: 'EXPIRED' }),
      marta,
    ];
    const group = officialGroup({ name: 'Ogrody 33 Club', runBy: marta });
    club.groups = [group];
    await signIn(page);
    await page.goto(`/groups/${group.id}`);

    await expect(page.getByRole('heading', { name: 'Ogrody 33 Club' })).toBeVisible();
    await expect(page.getByRole('radio')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Hand over', exact: true })).toHaveCount(0);
    await expect(page.getByRole('main')).toContainText('There is nobody else to give it to yet.');
    await page.getByRole('link', { name: 'Invite an administrator first' }).click();
    await expect(page.getByRole('heading', { name: 'Administrators' })).toBeVisible();
  });

  test('handing it to somebody removed meanwhile is refused, and the page catches up', async ({
    page,
    stub,
    club,
  }) => {
    const tomek = active('Tomek K.', 'tomek.k@gmail.com');
    club.administrators = [tomek];
    const group = officialGroup({ name: 'Ogrody 33 Club' });
    club.groups = [group];
    await signIn(page);
    await page.goto(`/groups/${group.id}`);
    await page.getByRole('radio', { name: /Tomek K\./ }).check();

    // Another tab removes Tomek before the desk confirms.
    club.administrators = [];
    await page.getByRole('button', { name: 'Hand over', exact: true }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Hand over' }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "Tomek K. isn't one of your active administrators any more. Choose someone else.",
    );
    await expect(page.getByRole('link', { name: 'Invite an administrator first' })).toBeVisible();
    await expect(page.getByRole('main')).toContainText('There is nobody to give it to yet.');
    await expect(page).toHaveURL(new RegExp(`/groups/${group.id}$`));
    expect(stub.requests('put', '/api/v1/club/groups/{group_id}/administrator')).toHaveLength(1);
    expect(club.groups[0]?.administrator_id).toBeNull();
  });

  test('a handover the backend never answered says so, and the choice stays', async ({
    page,
    stub,
    club,
  }) => {
    club.administrators = [active('Tomek K.', 'tomek.k@gmail.com')];
    const group = officialGroup({ name: 'Ogrody 33 Club' });
    club.groups = [group];
    stub.on('put', '/api/v1/club/groups/{group_id}/administrator', () => ({ status: 'drop' }));
    await signIn(page);
    await page.goto(`/groups/${group.id}`);
    const tomek = page.getByRole('radio', { name: /Tomek K\./ });
    await tomek.check();
    await page.getByRole('button', { name: 'Hand over', exact: true }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Hand over' }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "We couldn't reach the server. Try again in a moment.",
    );
    await expect(tomek).toBeChecked();
    await expect(page.getByRole('button', { name: 'Hand over', exact: true })).toBeEnabled();
    await expect(page.getByRole('dialog')).toBeHidden();
  });

  test('a group that is none of the club’s is nothing at this address', async ({ page, club }) => {
    club.groups = [officialGroup({ name: 'Ogrody 33 Club' })];
    await signIn(page);
    await page.goto('/groups/0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e99');
    await expect(page.getByRole('heading', { name: 'Nothing at this address' })).toBeVisible();
  });
});

test.describe('Join requests', () => {
  /** Every row in *Want to join*: each one answers somebody. */
  function requests(page: Page) {
    return page
      .getByRole('listitem')
      .filter({ has: page.getByRole('button', { name: /^Approve / }) });
  }

  /** The row in *Want to join* that a person's nickname, or the fallback, heads. */
  function requestOf(page: Page, name: string) {
    return requests(page).filter({ hasText: name });
  }

  test('with nobody running it, the desk lets one in and turns one away, and the table counts', async ({
    page,
    stub,
    club,
  }) => {
    const rafa = joinRequest({
      nickname: 'rafa.p',
      levels: [
        { sport: 'PADEL', level: 2.456 },
        { sport: 'TENNIS', level: 3.1 },
      ],
    });
    const kasia = joinRequest({ nickname: 'kasia_l' });
    const group = officialGroup({
      name: 'Ogrody 33 Club',
      member_count: 5,
      whatsapp_size: 48,
      requests: [rafa, kasia],
    });
    club.groups = [group];
    await openGroups(page);
    await expect(rowOf(page, 'Ogrody 33 Club').getByText('2 waiting')).toBeVisible();
    await rowOf(page, 'Ogrody 33 Club').getByRole('link').click();

    await expect(page.getByRole('heading', { name: 'Want to join · 2' })).toBeVisible();
    await expect(page.getByRole('main')).toContainText(
      'Nobody runs this group right now, so they wait for you. Answer them here, or hand the ' +
        'group over below.',
    );
    // In the order they asked, each by their whole nickname and never with an @ (ADR-0199 §5),
    // over their Levels as the app writes them.
    await expect(requests(page)).toHaveText([
      /^rafa\.p\s*Padel 2,46 · Tennis 3,10/,
      /^kasia_l\s*Not rated in any sport yet/,
    ]);

    await page.getByRole('button', { name: 'Approve rafa.p' }).click();
    await expect(page.getByRole('heading', { name: 'Want to join · 1' })).toBeVisible();
    await expect(requestOf(page, 'rafa.p')).toHaveCount(0);

    await page.getByRole('button', { name: 'Decline kasia_l' }).click();
    await expect(page.getByRole('heading', { name: /Want to join/ })).toHaveCount(0);

    expect(
      stub
        .requests('post', '/api/v1/club/groups/{group_id}/requests/{player_id}/approve')
        .map(({ params }) => params),
    ).toEqual([{ group_id: group.id, player_id: rafa.player_id }]);
    expect(
      stub
        .requests('post', '/api/v1/club/groups/{group_id}/requests/{player_id}/decline')
        .map(({ params }) => params),
    ).toEqual([{ group_id: group.id, player_id: kasia.player_id }]);
    // Answering is not running it: the group still needs an administrator.
    await expect(page.getByText('needs an administrator')).toBeVisible();

    await page.getByRole('navigation').getByRole('link', { name: 'Groups' }).click();
    await expect(rowOf(page, 'Ogrody 33 Club').getByRole('cell')).toHaveText([
      'needs an administrator',
      '6',
      '6 of 48 · 13%',
      '0',
    ]);
  });

  test('a group somebody runs says they answer in the app, and the desk can answer too', async ({
    page,
    club,
  }) => {
    const marta = active('Marta Wójcik', 'marta@ogrody33.pl');
    club.administrators = [marta];
    const group = officialGroup({
      name: 'Ogrody 33 Club',
      runBy: marta,
      requests: [joinRequest({ nickname: 'rafa.p' })],
    });
    club.groups = [group];
    await signIn(page);
    await page.goto(`/groups/${group.id}`);

    await expect(page.getByRole('heading', { name: 'Want to join · 1' })).toBeVisible();
    await expect(page.getByRole('main')).toContainText(
      'Marta Wójcik answers them in the app, and you can answer them here too.',
    );
    await page.getByRole('button', { name: 'Approve rafa.p' }).click();
    await expect(page.getByRole('heading', { name: /Want to join/ })).toHaveCount(0);
    await expect(page.getByRole('main')).toContainText(/Administrator\s*Marta Wójcik/);
  });

  test('an answer the administrator gave first is said, and the page catches up', async ({
    page,
    club,
  }) => {
    const group = officialGroup({
      name: 'Ogrody 33 Club',
      requests: [joinRequest({ nickname: 'rafa.p' })],
    });
    club.groups = [group];
    await signIn(page);
    await page.goto(`/groups/${group.id}`);
    await expect(page.getByRole('heading', { name: 'Want to join · 1' })).toBeVisible();

    // The administrator lets him in from the app before the desk presses.
    club.groups = [{ ...group, member_count: 1, requests: [] }];
    await page.getByRole('button', { name: 'Approve rafa.p' }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "rafa.p isn't waiting any more: somebody answered first.",
    );
    await expect(page.getByRole('heading', { name: /Want to join/ })).toHaveCount(0);
  });

  test('somebody who can no longer be named still waits, and is answered as the fallback', async ({
    page,
    stub,
    club,
  }) => {
    const nobody = joinRequest({ nickname: null });
    const group = officialGroup({ name: 'Ogrody 33 Club', requests: [nobody] });
    club.groups = [group];
    await signIn(page);
    await page.goto(`/groups/${group.id}`);

    // The fallback Bookings reads too, and the person is answered by it (ADR-0199 §5).
    await expect(requests(page)).toHaveText([/^A player\s*Not rated in any sport yet/]);
    await page.getByRole('button', { name: 'Decline A player' }).click();
    await expect(page.getByRole('heading', { name: /Want to join/ })).toHaveCount(0);
    expect(
      stub
        .requests('post', '/api/v1/club/groups/{group_id}/requests/{player_id}/decline')
        .map(({ params }) => params),
    ).toEqual([{ group_id: group.id, player_id: nobody.player_id }]);
  });

  test('nobody waiting draws no card', async ({ page, club }) => {
    const group = officialGroup({ name: 'Ogrody 33 Club' });
    club.groups = [group];
    await signIn(page);
    await page.goto(`/groups/${group.id}`);

    await expect(page.getByRole('heading', { name: 'Ogrody 33 Club' })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Want to join/ })).toHaveCount(0);
  });
});
