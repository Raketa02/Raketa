/**
 * WCAG 2.1 arithmetic, for the tests that derive this system's published ratios.
 *
 * **In `test-support/` because it is not app code.** The app draws colours; it never scores
 * them, for the reason `bandEdges.test.ts` gives — a `theme.ts` that checked its own
 * arithmetic would be the app refusing to launch over a drawing detail, and a red build is
 * where a human reconciles it. This folder is where the things that ship to no build live,
 * beside `transport.ts` and `platform.ts`.
 *
 * It exists because there are now **two** tables of derived ratios — the court's four rows
 * and the poster's two — and this file is what keeps them one computation. The shared UI
 * README's rule is the argument: *the prototype kept a second copy of its card, bar and
 * popover, and recorded that they had drifted.* Two copies of a luminance formula drift the
 * same way, and more quietly, because the numbers still look like numbers.
 */

/** Channels, 0–255. */
export type Rgb = readonly [number, number, number];

/** A hex or an `rgb()`/`rgba()` string, which is every colour form `theme.ts` uses. */
export function parse(value: string): { readonly rgb: Rgb; readonly alpha: number } {
  const hex = /^#([0-9a-f]{6})$/i.exec(value);
  if (hex?.[1]) {
    const n = Number.parseInt(hex[1], 16);
    return { rgb: [(n >> 16) & 255, (n >> 8) & 255, n & 255], alpha: 1 };
  }
  const rgba = /^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)$/i.exec(value);
  if (!rgba) throw new Error(`not a colour this file can read: ${value}`);
  return {
    rgb: [Number(rgba[1]), Number(rgba[2]), Number(rgba[3])],
    alpha: rgba[4] === undefined ? 1 : Number(rgba[4]),
  };
}

/** `over` composited onto `under`. Straight alpha, sRGB channels. */
export function composite(over: Rgb, alpha: number, under: Rgb): Rgb {
  const mix = (i: 0 | 1 | 2) => alpha * over[i] + (1 - alpha) * under[i];
  return [mix(0), mix(1), mix(2)];
}

/** WCAG 2.1 relative luminance. */
export function luminance([r, g, b]: Rgb): number {
  const channel = (c: number) => {
    const s = c / 255;
    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

/** WCAG 2.1 contrast ratio, rounded to the two decimals the document prints. */
export function contrast(a: Rgb, b: Rgb): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return Math.round(((hi + 0.05) / (lo + 0.05)) * 100) / 100;
}

/**
 * The sRGB-HSL hue angle, in degrees.
 *
 * The measure every hue bound in this system is stated in — `red` is at 6°, `volt` at 69°,
 * `mint` at 163° — so a bound checked in any other space would be checked against numbers
 * nothing else uses.
 */
export function hueAngle([r, g, b]: Rgb): number {
  const [red, green, blue] = [r / 255, g / 255, b / 255] as const;
  const max = Math.max(red, green, blue);
  const span = max - Math.min(red, green, blue);
  if (span === 0) return 0;

  const sextant =
    max === red
      ? ((green - blue) / span) % 6
      : max === green
        ? (blue - red) / span + 2
        : (red - green) / span + 4;
  const degrees = sextant * 60;
  return degrees < 0 ? degrees + 360 : degrees;
}

/** The shorter way round the colour wheel, which is the only distance a hue bound means. */
export function hueDistance(a: number, b: number): number {
  const apart = Math.abs(a - b) % 360;
  return Math.min(apart, 360 - apart);
}
