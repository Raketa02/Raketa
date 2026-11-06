import 'server-only';

import { ImageResponse } from 'next/og';

import { PREVIEW_TOKENS } from '@/ui/tokens';

import type { Face } from './mappers';

/**
 * **The friend link's picture: the owner's face, square**, which the page draws beside its heading
 * and a messenger beside the preview's title. Full bleed, because a messenger rounds or crops a
 * thumbnail itself, and the photograph **fills** the square, cut to its middle, since the backend
 * keeps a photograph's own shape.
 *
 * Redrawn from the photograph on every request, never kept: the link to it is signed for minutes.
 */

/**
 * A new photograph, or a New link that turns this one off, redraws or ends the face, so the
 * picture is never kept for good (`ImageResponse` would say `immutable` for a year). Ten minutes,
 * as the group's tile, and **`private`**, unlike the tile: a person's face is kept by whoever
 * asked for it and by no cache in between, which could go on serving it after a New link.
 */
const CACHING = 'private, max-age=600';

export function faceImage(face: Face): ImageResponse {
  const side = PREVIEW_TOKENS.faceSide;
  return new ImageResponse(
    <div style={{ display: 'flex', width: '100%', height: '100%' }}>
      {/* Satori draws a picture from an <img> and nothing else. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={face.source} alt="" width={side} height={side} style={{ objectFit: 'cover' }} />
    </div>,
    { width: side, height: side, headers: { 'cache-control': CACHING } },
  );
}
