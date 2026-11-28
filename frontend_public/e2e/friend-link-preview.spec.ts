import type { Page } from '@playwright/test';

import { expect, test } from './fixtures';
import { photograph, portrait } from './photographs';
import { headOf, MESSENGERS, sizeOf } from './reading';
import { refusal } from './stub/backend';
import { FRIEND_LINK_PATH, tomek } from './stub/friends';
import { SITE_URL } from './suite';

/**
 * **The friend link's preview** (#755): Tomek pastes his link into a WhatsApp chat, and the card
 * says *Tomek invited you to play on Rakieta* beside his face. The tags are read from the HTML the
 * server sends (ADR-0187 §4); the picture is his photograph, drawn square by this site from a link
 * the backend signs for minutes, so it is read afresh for every picture.
 */

/** The colour at each corner of the picture at `/face/<code>`, as the browser decodes it. */
async function cornersOf(page: Page, code: string): Promise<number[][]> {
  return page.evaluate(async (src) => {
    const image = new Image();
    image.src = src;
    await image.decode();
    const canvas = document.createElement('canvas');
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext('2d')!;
    context.drawImage(image, 0, 0);
    const last = { x: canvas.width - 1, y: canvas.height - 1 };
    return [
      [0, 0],
      [last.x, 0],
      [0, last.y],
      [last.x, last.y],
    ].map(([x, y]) => [...context.getImageData(x!, y!, 1, 1).data.slice(0, 3)]);
  }, `/face/${code}`);
}

/** Within a JPEG's rounding of `[r, g, b]`. */
function near(colour: number[], [r, g, b]: [number, number, number]): boolean {
  const [cr = -1, cg = -1, cb = -1] = colour;
  return Math.abs(cr - r) <= 12 && Math.abs(cg - g) <= 12 && Math.abs(cb - b) <= 12;
}

for (const userAgent of MESSENGERS) {
  test(`the friend link's preview tags are in the head the server sends, for ${userAgent.split('/')[0]}`, async ({
    page,
    request,
    friendLinks,
  }) => {
    friendLinks.seat('k7pq2mxa', tomek({ photo: await portrait(page) }));

    const { status, title, tags } = await headOf(request, '/f/k7pq2mxa', userAgent);

    expect(status).toBe(200);
    expect(title).toBe('Tomek invited you to play on Rakieta');
    expect(tags.get('og:title')).toBe('Tomek invited you to play on Rakieta');
    expect(tags.get('og:description')).toBe('Tomek wants to be your friend');
    expect(tags.get('description')).toBe('Tomek wants to be your friend');
    expect(tags.get('og:site_name')).toBe('Rakieta');
    // Absolute, at the address the site is reached at, and outside /f/, which the app claims.
    expect(tags.get('og:url')).toBe(`${SITE_URL}/f/k7pq2mxa`);
    expect(tags.get('og:image')).toBe(`${SITE_URL}/face/k7pq2mxa`);
    expect(tags.get('og:image:width')).toBe('300');
    expect(tags.get('og:image:height')).toBe('300');
    expect(tags.get('og:image:alt')).toBe('Tomek');
    expect(tags.get('twitter:card')).toBe('summary');
  });
}

test('a page that names somebody and shows their face asks never to be listed', async ({
  request,
  friendLinks,
}) => {
  friendLinks.seat('k7pq2mxa');

  const { tags } = await headOf(request, '/f/k7pq2mxa', MESSENGERS[0]!);

  expect(tags.get('robots')).toBe('noindex, nofollow');
});

test('somebody with no photograph is previewed without a picture', async ({
  request,
  friendLinks,
}) => {
  friendLinks.seat('k7pq2mxa', tomek({ photo: null }));

  const { status, tags } = await headOf(request, '/f/k7pq2mxa', MESSENGERS[0]!);

  expect(status).toBe(200);
  expect(tags.get('og:title')).toBe('Tomek invited you to play on Rakieta');
  expect(tags.has('og:image')).toBe(false);
  expect((await request.get('/face/k7pq2mxa')).status()).toBe(404);
});

test('a dead link has no preview card: it says Nothing at that link, with no image', async ({
  request,
}) => {
  const { status, title, tags } = await headOf(request, '/f/zzzzzzzz', MESSENGERS[0]!);

  expect(status).toBe(404);
  expect(title).toBe('Nothing at that link · Rakieta');
  expect(tags.has('og:image')).toBe(false);
  expect(tags.has('og:title')).toBe(false);
});

test('the page and its preview tags ask the backend once between them', async ({
  request,
  stub,
  friendLinks,
}) => {
  friendLinks.seat('k7pq2mxa');

  await headOf(request, '/f/k7pq2mxa', MESSENGERS[0]!);

  expect(stub.requests('get', FRIEND_LINK_PATH)).toHaveLength(1);
});

test('the face is a square PNG', async ({ page, request, friendLinks }) => {
  friendLinks.seat('k7pq2mxa', tomek({ photo: await portrait(page) }));

  const response = await request.get('/face/k7pq2mxa');

  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toBe('image/png');
  expect(sizeOf(await response.body())).toEqual({ width: 300, height: 300 });
});

test('the face is the photograph, filling the square: a wide one is cut to its middle', async ({
  page,
  friendLinks,
}) => {
  // Four times as wide as it is tall: the middle half is green, the edges red and blue, so a
  // square cut from its middle is green to every corner, and a stretched one is not.
  const green: [number, number, number] = [48, 131, 97];
  const middle = `rgb(${green.join(', ')})`;
  friendLinks.seat(
    'k7pq2mxa',
    tomek({
      photo: await photograph(page, {
        width: 1200,
        height: 300,
        bands: ['rgb(211, 77, 46)', middle, middle, 'rgb(61, 90, 153)'],
      }),
    }),
  );
  await page.goto('/f/k7pq2mxa');

  const corners = await cornersOf(page, 'k7pq2mxa');

  for (const corner of corners) {
    expect(near(corner, green), `a corner is ${corner.join(', ')}`).toBe(true);
  }
});

test('the face is read afresh for every picture: a signed link is never kept', async ({
  page,
  request,
  stub,
  friendLinks,
}) => {
  friendLinks.seat('k7pq2mxa', tomek({ photo: await portrait(page) }));

  expect((await request.get('/face/k7pq2mxa')).status()).toBe(200);
  stub.expireSignedLinks();
  expect((await request.get('/face/k7pq2mxa')).status()).toBe(200);

  expect(stub.requests('get', FRIEND_LINK_PATH)).toHaveLength(2);
  const opened = stub.storageOpened();
  expect(opened).toHaveLength(2);
  expect(new Set(opened).size).toBe(2);
});

test('a new photograph or a New link redraws the face: nothing may keep it for good', async ({
  page,
  request,
  friendLinks,
}) => {
  friendLinks.seat('k7pq2mxa', tomek({ photo: await portrait(page) }));

  const response = await request.get('/face/k7pq2mxa');

  expect(response.status()).toBe(200);
  const caching = response.headers()['cache-control'] ?? '';
  expect(caching).not.toContain('immutable');
  expect(Number(/max-age=(\d+)/.exec(caching)?.[1] ?? '0')).toBeLessThanOrEqual(600);
});

test('a replaced link has no face', async ({ page, request, friendLinks }) => {
  friendLinks.seat('k7pq2mxa', tomek({ photo: await portrait(page) }));
  expect((await request.get('/face/k7pq2mxa')).status()).toBe(200);

  friendLinks.replace('k7pq2mxa');

  expect((await request.get('/face/k7pq2mxa')).status()).toBe(404);
});

test('a face the backend or the storage could not give is not drawn', async ({ request, stub }) => {
  stub.on('get', FRIEND_LINK_PATH, () => ({
    status: 200,
    body: { nickname: 'Tomek', photo_url: stub.signedLink('photos/deleted.jpg') },
  }));
  expect((await request.get('/face/k7pq2mxa')).status()).toBe(500);

  stub.on('get', FRIEND_LINK_PATH, () => ({ status: 503, body: refusal('service_unavailable') }));
  expect((await request.get('/face/k7pq2mxa')).status()).toBe(500);
});
