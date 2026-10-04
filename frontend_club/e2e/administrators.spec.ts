import type { Page } from '@playwright/test';

import { expect, signIn, test } from './fixtures';
import { administrator, DAY_MS, fromNow } from './stub/club';

/**
 * **The Administrators page** (#523, club mocks 2–4 and 14): the club names the people who run
 * its groups in the app, and sees where each one stands.
 */

const MARTA = {
  name: 'Marta Wójcik',
  email: 'marta@ogrody33.pl',
} as const;

/** Marta took up her invitation and ran her groups three days ago: club mock 2's row. */
function activeMarta() {
  return administrator({
    ...MARTA,
    status: 'ACTIVE',
    last_used_at: fromNow(-3 * DAY_MS),
    expires_at: null,
    can_reset_password: true,
  });
}

async function openAdministrators(page: Page) {
  await signIn(page);
  await page.getByRole('navigation').getByRole('link', { name: 'Administrators' }).click();
  await expect(page.getByRole('heading', { name: 'Administrators' })).toBeVisible();
}

/** The row a person's name heads. */
function rowOf(page: Page, name: string) {
  return page.getByRole('row').filter({ has: page.getByRole('rowheader', { name, exact: true }) });
}

test.describe('Administrators', () => {
  test('the header says who they are, and each row names one of them', async ({ page, club }) => {
    club.administrators = [activeMarta()];
    await openAdministrators(page);

    await expect(page.getByText('People who run your groups in the app')).toBeVisible();
    await expect(page.getByRole('button', { name: '+ Add administrator' })).toBeVisible();

    const table = page.getByRole('table');
    await expect(table.getByRole('columnheader')).toHaveText([
      'Administrator',
      'Email',
      'Groups',
      'Status',
      'Actions',
    ]);
    const marta = rowOf(page, 'Marta Wójcik');
    await expect(marta.getByRole('cell')).toHaveText([
      'marta@ogrody33.pl',
      'none yet',
      /active\s*this week/,
      /Reset password\s*Remove/,
    ]);
    await expect(marta.getByText('marta@ogrody33.pl')).toHaveCSS('font-family', /IBM Plex Mono/);
  });

  test('each status says when, in the words the desk reads', async ({ page, club }) => {
    const HOUR_MS = DAY_MS / 24;
    club.administrators = [
      administrator({
        name: 'Ania Today',
        email: 'ania@ogrody33.pl',
        status: 'ACTIVE',
        last_used_at: fromNow(-2 * HOUR_MS),
        expires_at: null,
      }),
      administrator({
        name: 'Bartek Weeks',
        email: 'bartek@ogrody33.pl',
        status: 'ACTIVE',
        last_used_at: fromNow(-23 * DAY_MS),
        expires_at: null,
      }),
      administrator({
        name: 'Celina Never',
        email: 'celina@ogrody33.pl',
        status: 'ACTIVE',
        last_used_at: null,
        expires_at: null,
      }),
      // Sent a minute ago: 71 hours and 59 minutes are three days, as the banner promised.
      administrator({
        name: 'Darek Invited',
        email: 'darek@ogrody33.pl',
        expires_at: fromNow(72 * HOUR_MS - 60_000),
      }),
      administrator({
        name: 'Ewa Lapsed',
        email: 'ewa@ogrody33.pl',
        status: 'EXPIRED',
        expires_at: fromNow(-HOUR_MS),
      }),
      administrator({
        name: 'Filip Lapsed',
        email: 'filip@ogrody33.pl',
        status: 'EXPIRED',
        expires_at: fromNow(-(2 * DAY_MS + 5 * HOUR_MS)),
      }),
      activeMarta(),
    ];
    await openAdministrators(page);

    const status = (name: string) => rowOf(page, name).getByRole('cell').nth(2);
    await expect(status('Ania Today')).toHaveText(/^active\s*today$/);
    await expect(status('Marta Wójcik')).toHaveText(/^active\s*this week$/);
    await expect(status('Bartek Weeks')).toHaveText(/^active\s*3 weeks ago$/);
    await expect(status('Celina Never')).toHaveText(/^active$/);
    await expect(status('Darek Invited')).toHaveText(/^invited\s*expires in 3 d$/);
    await expect(status('Ewa Lapsed')).toHaveText(/^expired\s*0 d ago$/);
    await expect(status('Filip Lapsed')).toHaveText(/^expired\s*2 d ago$/);
  });

  test('the groups someone runs open from a dropdown, and nobody else has any yet', async ({
    page,
    club,
  }) => {
    club.administrators = [
      {
        ...activeMarta(),
        groups: [
          { id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e01', name: 'Ogrody 33 Club' },
          { id: '0b8f5c1e-1c1d-4d2e-8f3a-5a6b7c8d9e02', name: 'Ogrody open play' },
        ],
      },
      administrator({ name: 'Tomek K.', email: 'tomek.k@gmail.com' }),
    ];
    await openAdministrators(page);

    const groups = rowOf(page, 'Marta Wójcik').getByRole('cell').nth(1);
    await expect(groups.getByText('2 groups')).toBeVisible();
    await expect(groups.getByText('Ogrody open play')).toBeHidden();
    await groups.getByText('2 groups').click();
    await expect(groups.getByRole('listitem')).toHaveText(['Ogrody 33 Club', 'Ogrody open play']);
    await expect(rowOf(page, 'Tomek K.').getByRole('cell').nth(1)).toHaveText('none yet');
  });

  test('+ Add administrator opens a name-and-email form in its place', async ({ page, club }) => {
    void club;
    await openAdministrators(page);
    const add = page.getByRole('button', { name: '+ Add administrator' });
    await add.click();

    await expect(add).toBeHidden();
    const name = page.getByLabel('Name', { exact: true });
    const email = page.getByLabel('Email', { exact: true });
    const send = page.getByRole('button', { name: 'Send invitation', exact: true });
    await expect(name).toBeFocused();
    await expect(name).toHaveAttribute('placeholder', 'Full name');
    await expect(
      page.getByText(
        'Raketa emails them. They set their own password in the app; if the email already has a ' +
          'Raketa account, they just accept.',
      ),
    ).toBeVisible();

    // Disabled until both are valid.
    await expect(send).toBeDisabled();
    await name.fill('Marta Wójcik');
    await expect(send).toBeDisabled();
    await email.fill('marta@ogrody33');
    await expect(send).toBeDisabled();
    await email.fill('marta@ogrody33.pl');
    await expect(send).toBeEnabled();
    await name.fill('M');
    await expect(send).toBeDisabled();

    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(name).toBeHidden();
    await add.click();
    await expect(name).toHaveValue('');
    await expect(email).toHaveValue('');
  });

  test('Send invitation says so in a banner, and the table lists them as invited', async ({
    page,
    stub,
    club,
  }) => {
    club.administrators = [activeMarta()];
    await openAdministrators(page);
    await page.getByRole('button', { name: '+ Add administrator' }).click();
    await page.getByLabel('Name', { exact: true }).fill('  Tomek   Kowalski ');
    await page.getByLabel('Email', { exact: true }).fill('tomek.k@gmail.com');
    await page.getByRole('button', { name: 'Send invitation', exact: true }).click();

    const banner = page.getByRole('status').filter({ hasText: /invitation sent/i });
    await expect(banner).toContainText(/^Invitation sent · valid 72 hours/i);
    await expect(banner).toContainText('Tomek Kowalski · tomek.k@gmail.com');
    await expect(banner.getByText('tomek.k@gmail.com')).toHaveCSS('font-family', /IBM Plex Mono/);
    // Whom it went to is the whole message: the email explains itself, and a line about a code
    // was wrong for an existing account, whose email carries none (#529 I2).
    await expect(banner).not.toContainText('emailed them');
    expect(stub.requests('post', '/api/v1/club/administrators').map((r) => r.body)).toEqual([
      { name: 'Tomek Kowalski', email: 'tomek.k@gmail.com' },
    ]);

    await expect(page.getByLabel('Name', { exact: true })).toBeHidden();
    await expect(page.getByRole('button', { name: '+ Add administrator' })).toBeVisible();
    await expect(rowOf(page, 'Tomek Kowalski').getByRole('cell')).toHaveText([
      'tomek.k@gmail.com',
      'none yet',
      /^invited\s*expires in 3 d$/,
      /^Resend invitation\s*Remove$/,
    ]);

    await banner.getByRole('button', { name: 'Done' }).click();
    await expect(banner).toBeHidden();
  });

  test("inviting someone already here shows the server's refusal in the form", async ({
    page,
    stub,
    club,
  }) => {
    club.administrators = [
      activeMarta(),
      administrator({ name: 'Tomek K.', email: 'tomek.k@gmail.com', status: 'EXPIRED' }),
    ];
    await openAdministrators(page);
    await page.getByRole('button', { name: '+ Add administrator' }).click();
    const email = page.getByLabel('Email', { exact: true });
    const send = page.getByRole('button', { name: 'Send invitation', exact: true });
    await page.getByLabel('Name', { exact: true }).fill('Marta Wójcik');
    await email.fill('Marta@ogrody33.pl');
    await send.click();

    await expect(page.getByText('They are already one of your administrators.')).toBeVisible();
    await expect(email).toHaveAttribute('aria-invalid', 'true');
    await expect(send).toBeDisabled();
    await expect(page.getByRole('main').getByRole('status')).toHaveCount(0);

    await email.fill('tomek.k@gmail.com');
    await expect(page.getByText('They are already one of your administrators.')).toBeHidden();
    await send.click();
    await expect(
      page.getByText(
        'They already have an invitation from your club. Resend it from the table instead.',
      ),
    ).toBeVisible();
    expect(stub.requests('post', '/api/v1/club/administrators')).toHaveLength(2);
    expect(club.administrators).toHaveLength(2);
  });

  test('a backend that does not answer is said over the form, and what was typed stays', async ({
    page,
    stub,
    club,
  }) => {
    void club;
    stub.on('post', '/api/v1/club/administrators', () => ({ status: 'drop' }));
    await openAdministrators(page);
    await page.getByRole('button', { name: '+ Add administrator' }).click();
    await page.getByLabel('Name', { exact: true }).fill('Tomek K.');
    await page.getByLabel('Email', { exact: true }).fill('tomek.k@gmail.com');
    await page.getByRole('button', { name: 'Send invitation', exact: true }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "We couldn't reach the server. Try again in a moment.",
    );
    await expect(page.getByLabel('Name', { exact: true })).toHaveValue('Tomek K.');
    await expect(page.getByRole('button', { name: 'Send invitation', exact: true })).toBeEnabled();
  });

  test('Resend invitation gives someone expired a fresh 72 hours', async ({ page, stub, club }) => {
    const tomek = administrator({
      name: 'Tomek K.',
      email: 'tomek.k@gmail.com',
      status: 'EXPIRED',
      expires_at: fromNow(-2 * DAY_MS),
    });
    club.administrators = [activeMarta(), tomek];
    await openAdministrators(page);
    const row = rowOf(page, 'Tomek K.');
    await expect(row.getByRole('cell').nth(2)).toHaveText(/^expired\s*2 d ago$/);
    await expect(
      rowOf(page, 'Marta Wójcik').getByRole('button', { name: 'Resend invitation' }),
    ).toHaveCount(0);

    await row.getByRole('button', { name: 'Resend invitation' }).click();

    const banner = page.getByRole('status').filter({ hasText: /invitation sent/i });
    await expect(banner).toContainText(/^Invitation sent · valid 72 hours/i);
    await expect(banner).toContainText('Tomek K. · tomek.k@gmail.com');
    await expect(row.getByRole('cell').nth(2)).toHaveText(/^invited\s*expires in 3 d$/);
    expect(
      stub
        .requests('post', '/api/v1/club/administrators/{administrator_id}/invitation')
        .map((request) => request.params.administrator_id),
    ).toEqual([tomek.id]);
  });

  test('Reset password is only offered for an account that does nothing but administer', async ({
    page,
    stub,
    club,
  }) => {
    const marta = activeMarta();
    // Tomek's account is also a player's, and only he may recover it (ADR-0184 §6).
    const tomek = administrator({
      name: 'Tomek K.',
      email: 'tomek.k@gmail.com',
      status: 'ACTIVE',
      last_used_at: fromNow(-DAY_MS / 2),
      expires_at: null,
      can_reset_password: false,
    });
    club.administrators = [marta, tomek];
    await openAdministrators(page);

    await expect(rowOf(page, 'Tomek K.').getByRole('button')).toHaveText(['Remove']);
    const row = rowOf(page, 'Marta Wójcik');
    await row.getByRole('button', { name: 'Reset password' }).click();

    const banner = page.getByRole('status').filter({ hasText: /password reset/i });
    await expect(banner).toContainText(/^Password reset · new invitation valid 72 hours/i);
    await expect(banner).toContainText('Marta Wójcik · marta@ogrody33.pl');
    await expect(banner).toContainText(
      "Their password is cleared and they're signed out everywhere.",
    );
    await expect(row.getByRole('cell').nth(2)).toHaveText(/^invited\s*expires in 3 d$/);
    await expect(row.getByRole('button', { name: 'Resend invitation' })).toBeVisible();
    expect(
      stub
        .requests('post', '/api/v1/club/administrators/{administrator_id}/password-reset')
        .map((request) => request.params.administrator_id),
    ).toEqual([marta.id]);
  });

  test('Remove asks first, and only a confirmed removal reaches the backend', async ({
    page,
    stub,
    club,
  }) => {
    const tomek = administrator({ name: 'Tomek K.', email: 'tomek.k@gmail.com' });
    club.administrators = [activeMarta(), tomek];
    await openAdministrators(page);
    const remove = rowOf(page, 'Tomek K.').getByRole('button', { name: 'Remove' });
    const dialog = page.getByRole('dialog', { name: 'Remove Tomek K.?' });

    await remove.click();
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText('Their groups stay, marked needs an administrator');
    await expect(dialog).toContainText('Raketa emails them to say so.');
    await dialog.getByRole('button', { name: 'Cancel' }).click();
    await expect(dialog).toBeHidden();

    await remove.click();
    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();
    expect(stub.requests('delete', '/api/v1/club/administrators/{administrator_id}')).toEqual([]);
    await expect(rowOf(page, 'Tomek K.')).toBeVisible();

    await remove.click();
    await dialog.getByRole('button', { name: 'Remove' }).click();

    await expect(dialog).toBeHidden();
    await expect(rowOf(page, 'Tomek K.')).toHaveCount(0);
    await expect(rowOf(page, 'Marta Wójcik')).toBeVisible();
    expect(
      stub
        .requests('delete', '/api/v1/club/administrators/{administrator_id}')
        .map((request) => request.params.administrator_id),
    ).toEqual([tomek.id]);
  });

  test('an act on a row that changed elsewhere is refused over the table, which catches up', async ({
    page,
    club,
  }) => {
    const marta = activeMarta();
    const tomek = administrator({
      name: 'Tomek K.',
      email: 'tomek.k@gmail.com',
      status: 'EXPIRED',
      expires_at: fromNow(-DAY_MS),
    });
    club.administrators = [marta, tomek];
    await openAdministrators(page);
    const refused = page.getByRole('main').getByRole('alert');

    // Tomek takes his invitation up in the app while the page is open.
    club.administrators = [
      marta,
      { ...tomek, status: 'ACTIVE', last_used_at: fromNow(0), expires_at: null },
    ];
    await rowOf(page, 'Tomek K.').getByRole('button', { name: 'Resend invitation' }).click();
    await expect(refused).toHaveText(
      'Tomek K. has already accepted, so there is no invitation to send again.',
    );
    await expect(rowOf(page, 'Tomek K.').getByRole('cell').nth(2)).toHaveText(/^active\s*today$/);
    await expect(page.getByRole('main').getByRole('status')).toHaveCount(0);

    // Then Marta starts playing, which takes Reset password away from the club.
    club.administrators = [{ ...marta, can_reset_password: false }, club.administrators[1]!];
    await rowOf(page, 'Marta Wójcik').getByRole('button', { name: 'Reset password' }).click();
    await expect(refused).toHaveText(
      'Marta Wójcik also plays on Raketa, so only they can reset their password, with Forgot ' +
        'password? in the app.',
    );
    await expect(rowOf(page, 'Marta Wójcik').getByRole('button')).toHaveText(['Remove']);
  });

  test('an act while the form is open says so at once, and the next answer replaces it', async ({
    page,
    club,
  }) => {
    const marta = activeMarta();
    const tomek = administrator({
      name: 'Tomek K.',
      email: 'tomek.k@gmail.com',
      status: 'EXPIRED',
      expires_at: fromNow(-DAY_MS),
    });
    club.administrators = [marta, tomek];
    await openAdministrators(page);
    await page.getByRole('button', { name: '+ Add administrator' }).click();
    await page.getByLabel('Name', { exact: true }).fill('Ola');

    await rowOf(page, 'Tomek K.').getByRole('button', { name: 'Resend invitation' }).click();
    const banner = page.getByRole('status').filter({ hasText: /invitation sent/i });
    await expect(banner).toContainText('Tomek K. · tomek.k@gmail.com');
    await expect(page.getByLabel('Name', { exact: true })).toHaveValue('Ola');

    // Marta starts playing before the club presses Reset password.
    club.administrators = [{ ...marta, can_reset_password: false }, club.administrators[1]!];
    await rowOf(page, 'Marta Wójcik').getByRole('button', { name: 'Reset password' }).click();
    await expect(page.getByRole('main').getByRole('alert')).toContainText(
      'Marta Wójcik also plays',
    );
    await expect(banner).toBeHidden();
  });

  test('a removal the backend never answered leaves the row, and says so', async ({
    page,
    stub,
    club,
  }) => {
    club.administrators = [activeMarta()];
    stub.on('delete', '/api/v1/club/administrators/{administrator_id}', () => ({ status: 'drop' }));
    await openAdministrators(page);
    await rowOf(page, 'Marta Wójcik').getByRole('button', { name: 'Remove' }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Remove' }).click();

    await expect(page.getByRole('main').getByRole('alert')).toHaveText(
      "We couldn't reach the server. Try again in a moment.",
    );
    await expect(rowOf(page, 'Marta Wójcik')).toBeVisible();
    await expect(page.getByRole('dialog')).toBeHidden();
  });
});
