import type { Page } from '@playwright/test';

import { expect, test } from './fixtures';
import { GROUP_PATH, linkedGroup } from './stub/groups';

/**
 * **The preview's image is the group's tile** (ADR-0187 §4): the picture a messenger draws beside
 * the group's name is the tile the page draws, and the app. Satori draws it from values in
 * `src/ui/tokens.ts`, which repeat `tokens.css`; these tests fail when the two disagree.
 */

/** The PNG's width and height, from its header. */
function sizeOf(png: Buffer): { width: number; height: number } {
  return { width: png.readUInt32BE(16), height: png.readUInt32BE(20) };
}

/**
 * What the browser sees in the image at `/preview/<code>`: the colour at one corner, and how many
 * pixels carry the letters' colour.
 */
async function pictureOf(page: Page, code: string, letters: string) {
  return page.evaluate(
    async ({ src, letters }) => {
      const image = new Image();
      image.src = src;
      await image.decode();
      const canvas = document.createElement('canvas');
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const context = canvas.getContext('2d')!;
      context.drawImage(image, 0, 0);
      const { data } = context.getImageData(0, 0, canvas.width, canvas.height);
      const [r, g, b] = data;
      const probe = document.createElement('span');
      probe.style.color = letters;
      document.body.append(probe);
      const [lr, lg, lb] = getComputedStyle(probe).color.match(/\d+/g)!.map(Number);
      probe.remove();
      let lettered = 0;
      for (let i = 0; i < data.length; i += 4) {
        if (data[i] === lr && data[i + 1] === lg && data[i + 2] === lb) lettered += 1;
      }
      return { corner: `rgb(${r}, ${g}, ${b})`, lettered };
    },
    { src: `/preview/${code}`, letters },
  );
}

/** The page's tile: its fill, and its letters' colour. */
async function tileOf(page: Page) {
  const tile = page.getByText('O3', { exact: true });
  return tile.evaluate((element) => {
    const style = getComputedStyle(element);
    return { fill: style.backgroundColor, letters: style.color };
  });
}

test('the preview image is a square PNG', async ({ request, groups }) => {
  groups.seat('k7pq2mxa');

  const response = await request.get('/preview/k7pq2mxa');

  expect(response.status()).toBe(200);
  expect(response.headers()['content-type']).toBe('image/png');
  expect(sizeOf(await response.body())).toEqual({ width: 600, height: 600 });
});

test('the preview image is drawn on the fill the page draws the tile on, for each of the eight', async ({
  page,
  groups,
}) => {
  for (const colour of [0, 1, 2, 3, 4, 5, 6, 7]) {
    // A code per group: the browser keeps a picture for as long as its caching allows.
    const code = `k7pq2mx${colour}`;
    groups.seat(code, linkedGroup({ monogram: { letters: 'O3', colour } }));
    await page.goto(`/join/${code}`);
    const tile = await tileOf(page);

    const picture = await pictureOf(page, code, tile.letters);

    expect(picture.corner, `colour key ${colour}`).toBe(tile.fill);
    expect(picture.lettered, `the letters on colour key ${colour}`).toBeGreaterThan(1_000);
  }
});

test('a tile that starts with a Polish letter is drawn in the same bold face as any other', async ({
  page,
  groups,
}) => {
  // Łagiewniki's Ł is an L with a stroke through it: in the tile's own bold face it covers more
  // than the L, and in a fallback face's thin one, far less.
  groups.seat('k7pq2mxl', linkedGroup({ monogram: { letters: 'L', colour: 0 } }));
  groups.seat('k7pq2mxs', linkedGroup({ monogram: { letters: 'Ł', colour: 0 } }));
  await page.goto('/join/k7pq2mxl');
  const { letters } = await page.getByText('L', { exact: true }).evaluate((element) => ({
    letters: getComputedStyle(element).color,
  }));

  const plain = await pictureOf(page, 'k7pq2mxl', letters);
  const stroked = await pictureOf(page, 'k7pq2mxs', letters);

  expect(stroked.lettered).toBeGreaterThan(plain.lettered);
});

test('a rename redraws the picture: nothing may keep an old tile for good', async ({
  request,
  groups,
}) => {
  groups.seat('k7pq2mxa');

  const response = await request.get('/preview/k7pq2mxa');

  expect(response.status()).toBe(200);
  const caching = response.headers()['cache-control'] ?? '';
  expect(caching).not.toContain('immutable');
  expect(Number(/max-age=(\d+)/.exec(caching)?.[1] ?? '0')).toBeLessThanOrEqual(600);
});

test('a dead link has no picture, and a code that could be nobody’s is not asked for', async ({
  request,
  stub,
}) => {
  expect((await request.get('/preview/zzzzzzzz')).status()).toBe(404);
  expect(stub.requests('get', GROUP_PATH)).toHaveLength(1);

  expect((await request.get('/preview/k7pq-2mxa')).status()).toBe(404);
  expect(stub.requests('get', GROUP_PATH)).toHaveLength(1);
});
