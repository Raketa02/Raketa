/**
 * **The values a picture needs**: the preview images', which Satori draws from inline styles and
 * which cannot read a CSS custom property. Every colour here repeats one in `tokens.css` under the
 * same name, and `e2e/preview-image.spec.ts` fails when the image and the page disagree. Besides
 * `tokens.css`, the only file in this app that writes a colour or a size.
 */
export const PREVIEW_TOKENS = {
  /** The image is square: a messenger draws it beside the name, as the app draws the tile. */
  side: 600,
  /** 0.37 of the side, as the app draws a tile's letters. */
  letters: 222,
  /** `--leading-none`. */
  leading: 1,
  /** `--weight-bold`, the tile's letters' weight. */
  weight: 700,
  /** `--colour-monogram-0` to `--colour-monogram-7`. */
  hues: ['#308361', '#87641a', '#213e50', '#9e3c2b', '#6a4c93', '#1e6b73', '#8c3f6e', '#3d5a99'],
  /** `--colour-on-monogram`. */
  onMonogram: '#ffffff',
  /**
   * **A link owner's face is smaller**: a photograph does not shrink as a PNG the way a tile's two
   * letters on one fill do, and a messenger draws either as a thumbnail. The page draws the same
   * picture at `--size-face`, which this covers at three pixels to a point with room to spare.
   */
  faceSide: 300,
} as const;
