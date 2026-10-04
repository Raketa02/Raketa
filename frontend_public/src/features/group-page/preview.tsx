import 'server-only';

import { readFile } from 'node:fs/promises';
import path from 'node:path';

import { ImageResponse } from 'next/og';

import { PREVIEW_TOKENS } from '@/ui/tokens';

import type { LinkedGroup } from './mappers';

/**
 * **The preview's image: the group's tile, square**, so a messenger draws it beside the group's
 * name as the app draws the tile beside it (play 38). Full bleed, because a messenger rounds or
 * crops a thumbnail itself.
 *
 * Satori draws it from inline styles, which cannot read a custom property, so its values are
 * `src/ui/tokens.ts`'s, and `e2e/preview-image.spec.ts` holds them to the page's.
 */

/**
 * Archivo Bold, the letters' face, **from the same package the page's type comes from**, so a
 * build fetches nothing. Latin and Latin Extended, because a Kraków group's name may start with
 * *Ł* or *Ż*. Satori reads woff but not woff2, and keeps one font per name and weight, so each
 * subset is a family of its own, listed in order.
 */
const SUBSETS = [
  { family: 'Archivo', subset: 'latin' },
  { family: 'Archivo Latin Extended', subset: 'latin-ext' },
];

const FAMILIES = SUBSETS.map(({ family }) => `"${family}"`).join(', ');

let fonts: Promise<{ family: string; data: Buffer }[]> | undefined;

function readFonts() {
  return Promise.all(
    SUBSETS.map(async ({ family, subset }) => ({
      family,
      data: await readFile(
        path.join(
          process.cwd(),
          'node_modules',
          '@fontsource',
          'archivo',
          'files',
          `archivo-${subset}-${PREVIEW_TOKENS.weight}-normal.woff`,
        ),
      ),
    })),
  );
}

/**
 * A rename redraws the tile, so the picture is never kept for good (`ImageResponse` would say
 * `immutable` for a year). Ten minutes lets a cache in front take a burst of fetches.
 */
const CACHING = 'public, max-age=600';

export async function previewImage(group: LinkedGroup): Promise<ImageResponse> {
  fonts ??= readFonts();
  const faces = await fonts;
  const { side, letters, leading, weight, hues, onMonogram } = PREVIEW_TOKENS;
  return new ImageResponse(
    <div
      style={{
        display: 'flex',
        width: '100%',
        height: '100%',
        alignItems: 'center',
        justifyContent: 'center',
        background: hues[group.monogram.hue],
        color: onMonogram,
        fontFamily: FAMILIES,
        fontSize: letters,
        fontWeight: weight,
        lineHeight: leading,
      }}
    >
      {group.monogram.letters}
    </div>,
    {
      width: side,
      height: side,
      fonts: faces.map(({ family, data }) => ({ name: family, data, weight, style: 'normal' })),
      headers: { 'cache-control': CACHING },
    },
  );
}
