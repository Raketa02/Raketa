/**
 * `qrcode`'s encoder, without its renderers — TypeScript needs telling where it is.
 *
 * Declared here because `qrPath.ts` is the only module that imports it. The package's own entry
 * is a renderer per platform — a canvas one for browsers, and one that writes PNGs through `fs` for
 * Node — and the app draws the matrix itself with `react-native-svg`, so it takes the core alone:
 * nothing a phone cannot load is ever in the bundle, whichever entry Metro would have picked.
 * The types are `@types/qrcode`'s.
 */
declare module 'qrcode/lib/core/qrcode' {
  import type { QRCode, QRCodeOptions } from 'qrcode';

  export function create(text: string, options?: QRCodeOptions): QRCode;
}
