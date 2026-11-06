import type { Page } from '@playwright/test';

/**
 * **A photograph as the backend stores one**: a JPEG of any shape, since the backend caps the long
 * edge and keeps the aspect. Drawn in the browser, left to right, as bands of colour of equal
 * width, so a test can tell which part of it a picture shows.
 */
export async function photograph(
  page: Page,
  { width, height, bands }: { width: number; height: number; bands: readonly string[] },
): Promise<Buffer> {
  const base64 = await page.evaluate(
    ({ width, height, bands }) => {
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext('2d')!;
      const band = width / bands.length;
      bands.forEach((colour, index) => {
        context.fillStyle = colour;
        context.fillRect(Math.floor(index * band), 0, Math.ceil(band), height);
      });
      return canvas.toDataURL('image/jpeg', 0.95).split(',')[1] ?? '';
    },
    { width, height, bands },
  );
  return Buffer.from(base64, 'base64');
}

/** A face as phones take one: taller than wide, in one colour. */
export function portrait(page: Page, colour = 'rgb(48, 131, 97)'): Promise<Buffer> {
  return photograph(page, { width: 300, height: 400, bands: [colour] });
}
