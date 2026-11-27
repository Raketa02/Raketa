import { expect, test } from './fixtures';
import { headOf, MESSENGERS } from './reading';
import { GROUP_PATH, linkedGroup } from './stub/groups';
import { SITE_URL } from './suite';

/**
 * **The preview a messenger draws** (#500 story 49): Marta posts the link into the padel WhatsApp
 * chat, and the card shows *Ogrody 33 Club*. A messenger runs no JavaScript and reads `<head>`, so
 * these tests read the HTML the server sends and nothing else (ADR-0187 §4).
 */

for (const userAgent of MESSENGERS) {
  test(`the group's preview tags are in the head the server sends, for ${userAgent.split('/')[0]}`, async ({
    request,
    groups,
  }) => {
    groups.seat('k7pq2mxa');

    const { status, title, tags } = await headOf(request, '/join/k7pq2mxa', userAgent);

    expect(status).toBe(200);
    expect(title).toBe('Ogrody 33 Club · Raketa');
    expect(tags.get('og:title')).toBe('Ogrody 33 Club');
    expect(tags.get('og:description')).toBe('Ogrody 33 · Grzegórzki · Padel · 11 members');
    expect(tags.get('description')).toBe('Ogrody 33 · Grzegórzki · Padel · 11 members');
    expect(tags.get('og:site_name')).toBe('Raketa');
    // Absolute, and at the address the site is reached at, which is not where the suite reaches it.
    expect(tags.get('og:url')).toBe(`${SITE_URL}/join/k7pq2mxa`);
    expect(tags.get('og:image')).toBe(`${SITE_URL}/preview/k7pq2mxa`);
    expect(tags.get('og:image:width')).toBe('600');
    expect(tags.get('og:image:height')).toBe('600');
    expect(tags.get('og:image:alt')).toBe('Ogrody 33 Club');
    expect(tags.get('twitter:card')).toBe('summary');
  });
}

test('the preview says every sport and the size, and keeps a name exactly as it was typed', async ({
  request,
  groups,
}) => {
  groups.seat(
    'k7pq2mxa',
    linkedGroup({
      name: 'Padel & "Tenis" <po pracy>',
      sports: ['PADEL', 'TENNIS'],
      member_count: 1,
    }),
  );

  const { tags } = await headOf(request, '/join/k7pq2mxa', MESSENGERS[0]!);

  expect(tags.get('og:title')).toBe('Padel & "Tenis" <po pracy>');
  expect(tags.get('og:description')).toBe('Ogrody 33 · Grzegórzki · Padel, Tennis · 1 member');
});

test('a group nobody is rated in yet is previewed without sports', async ({ request, groups }) => {
  groups.seat('k7pq2mxa', linkedGroup({ sports: [], member_count: 0 }));

  const { tags } = await headOf(request, '/join/k7pq2mxa', MESSENGERS[0]!);

  expect(tags.get('og:description')).toBe('Ogrody 33 · Grzegórzki · 0 members');
});

test('a dead link has no preview card: it says Nothing at that link, with no image', async ({
  request,
}) => {
  const { status, title, tags } = await headOf(request, '/join/zzzzzzzz', MESSENGERS[0]!);

  expect(status).toBe(404);
  expect(title).toBe('Nothing at that link · Raketa');
  expect(tags.has('og:image')).toBe(false);
  expect(tags.has('og:title')).toBe(false);
});

test('the page and its preview ask the backend once between them', async ({
  request,
  stub,
  groups,
}) => {
  groups.seat('k7pq2mxa');

  await headOf(request, '/join/k7pq2mxa', MESSENGERS[0]!);

  expect(stub.requests('get', GROUP_PATH)).toHaveLength(1);
});

test.describe('without JavaScript', () => {
  test.use({ javaScriptEnabled: false });

  test('the whole page is there', async ({ page, groups }) => {
    groups.seat('k7pq2mxa');

    await page.goto('/join/k7pq2mxa');

    await expect(page.getByRole('heading', { level: 1, name: 'Ogrody 33 Club' })).toBeVisible();
    await expect(page.getByText('11 members')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Open in Rakieta' })).toBeVisible();
  });
});
