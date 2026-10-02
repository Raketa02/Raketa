import { expect, signIn, test } from './fixtures';

/**
 * **The top bar** (#561, the screens B1): the pages a desk works in, and the club's name opening
 * the two pages about the club itself, *Details* and *Raketa settings*. Bookings and Money join
 * the bar with their own tickets.
 */

test.describe('The top bar', () => {
  test("lists the pages, and the club's name opens Details and Raketa settings", async ({
    page,
    club,
  }) => {
    void club;
    await signIn(page);
    const bar = page.getByRole('banner');
    const pages = bar.getByRole('navigation', { name: 'Club website' });
    await expect(pages.getByRole('link')).toHaveText([
      'Overview',
      'Courts & prices',
      'Groups',
      'Administrators',
    ]);

    const menu = bar.getByRole('button', { name: /Ogrody 33/ });
    await expect(menu).toHaveText('Ogrody 33 · Grzegórzki, Kraków');
    await expect(menu).toHaveAttribute('aria-expanded', 'false');
    await expect(bar.getByRole('link', { name: 'Details' })).toBeHidden();

    await menu.click();
    await expect(menu).toHaveAttribute('aria-expanded', 'true');
    await expect(bar.getByRole('list', { name: 'Ogrody 33' }).getByRole('link')).toHaveText([
      'Details',
      'Raketa settings',
    ]);

    await bar.getByRole('link', { name: 'Raketa settings' }).click();
    await expect(page).toHaveURL(/\/raketa-settings$/);
    await expect(page.getByRole('heading', { name: 'Raketa settings', level: 1 })).toBeVisible();
    // Leaving for the page closed the menu; opening it again marks where the desk is.
    await expect(menu).toHaveAttribute('aria-expanded', 'false');
    await menu.click();
    await expect(bar.getByRole('link', { name: 'Raketa settings' })).toHaveAttribute(
      'aria-current',
      'page',
    );

    await bar.getByRole('link', { name: 'Details' }).click();
    await expect(page.getByRole('heading', { name: 'Club details' })).toBeVisible();
  });

  test('Courts & prices opens from the bar, and says it is the page shown', async ({
    page,
    club,
  }) => {
    void club;
    await signIn(page);
    const pages = page.getByRole('navigation', { name: 'Club website' });
    await pages.getByRole('link', { name: 'Courts & prices' }).click();

    await expect(page).toHaveURL(/\/courts$/);
    await expect(page.getByRole('heading', { name: 'Courts & prices', level: 1 })).toBeVisible();
    await expect(pages.getByRole('link', { name: 'Courts & prices' })).toHaveAttribute(
      'aria-current',
      'page',
    );
  });

  test("the club's menu closes with Escape, back on its button, and with a click away", async ({
    page,
    club,
  }) => {
    void club;
    await signIn(page);
    const bar = page.getByRole('banner');
    const menu = bar.getByRole('button', { name: /Ogrody 33/ });

    await menu.click();
    await expect(bar.getByRole('link', { name: 'Details' })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(bar.getByRole('link', { name: 'Details' })).toBeHidden();
    await expect(menu).toBeFocused();

    await menu.click();
    await expect(bar.getByRole('link', { name: 'Details' })).toBeVisible();
    await page.getByRole('heading', { name: 'Overview' }).click();
    await expect(bar.getByRole('link', { name: 'Details' })).toBeHidden();
  });
});
