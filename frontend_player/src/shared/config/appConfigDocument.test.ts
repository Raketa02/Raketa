/**
 * The native configuration document, asserted to be a caller rather than a second table.
 *
 * `app.config.ts` is the one file in this app that is evaluated by **two** runtimes —
 * Node, when Expo resolves the config, and here. What a unit test can reach is the half
 * that matters architecturally: that the name it publishes is the identity function's
 * answer and not a string of its own, and that exactly one installable variant comes out
 * of it.
 *
 * What it *cannot* reach is the sweep across four environments: `babel-preset-expo`
 * substitutes `process.env.EXPO_PUBLIC_ENV` at transform time — that is the whole reason
 * `env.ts` spells its variables out — so the document under test is frozen at
 * `jest.config.js`'s value and reassigning it here would change nothing. The sweep is
 * `appIdentity.test.ts`'s, against the pure function, plus `npx expo config` per
 * environment by hand.
 */

import { readFileSync } from 'fs';
import { join } from 'path';
import { inflateSync } from 'zlib';

import appConfig from '../../../app.config';

import { theme } from '@/shared/ui/theme';

import { appIdentity } from './appIdentity';
import { APP_SCHEME } from './appLinks';
import { getEnv } from './env';

/**
 * The document registers sucrase's TypeScript require hook so that **Node** can load the
 * identity module when Expo resolves the config. Jest does not need it — its own resolver
 * reads `.ts` — and installing it here corrupts the source maps jest reads back, which
 * fails the suite before a single assertion runs. Stubbed to nothing, which is exactly
 * what the hook is worth inside a bundler.
 *
 * Written below the imports and still effective: `babel-plugin-jest-hoist` lifts a
 * `jest.mock` call above them, which is the whole reason it exists.
 */
jest.mock('sucrase/register/ts', () => ({}));

const config = appConfig();

/**
 * One configured plugin entry, as its `[name, options]` pair.
 *
 * A plugin listed as a bare string carries no options and would fail here, which is the
 * intent: the entries below exist *because* of what they configure.
 */
function pluginNamed(name: string): [string, Record<string, unknown>] {
  const entry = (config.plugins ?? []).find(
    (plugin) => Array.isArray(plugin) && plugin[0] === name,
  );

  if (!Array.isArray(entry)) throw new Error(`${name} is not configured in app.config.ts`);
  return [entry[0] as string, (entry[1] ?? {}) as Record<string, unknown>];
}

/**
 * Whether a PNG draws nothing at all: 8-bit RGBA, and every pixel's alpha nought.
 *
 * Read straight from the file's chunks — the image data inflated and each scanline un-filtered —
 * rather than through an image library, because the question is one byte per pixel.
 */
function everyPixelIsTransparent(png: Buffer): boolean {
  const SIGNATURE = '89504e470d0a1a0a';
  if (png.subarray(0, 8).toString('hex') !== SIGNATURE) return false;

  let width = 0;
  let height = 0;
  const data: Buffer[] = [];
  for (let at = 8; at < png.length;) {
    const length = png.readUInt32BE(at);
    const type = png.toString('latin1', at + 4, at + 8);
    const body = png.subarray(at + 8, at + 8 + length);
    if (type === 'IHDR') {
      width = body.readUInt32BE(0);
      height = body.readUInt32BE(4);
      const [bitDepth, colourType, , , interlace] = body.subarray(8, 13);
      if (bitDepth !== 8 || colourType !== 6 || interlace !== 0) return false;
    }
    if (type === 'IDAT') data.push(body);
    at += 12 + length;
  }

  const BYTES = 4;
  const stride = width * BYTES;
  const raw = inflateSync(Buffer.concat(data));
  let previous = Buffer.alloc(stride);
  for (let row = 0; row < height; row += 1) {
    const filter = raw[row * (stride + 1)];
    const line = Buffer.from(raw.subarray(row * (stride + 1) + 1, (row + 1) * (stride + 1)));
    for (let i = 0; i < stride; i += 1) {
      const left = i >= BYTES ? (line[i - BYTES] ?? 0) : 0;
      const up = previous[i] ?? 0;
      const upLeft = i >= BYTES ? (previous[i - BYTES] ?? 0) : 0;
      const paeth = () => {
        const p = left + up - upLeft;
        const [a, b, c] = [Math.abs(p - left), Math.abs(p - up), Math.abs(p - upLeft)];
        return a <= b && a <= c ? left : b <= c ? up : upLeft;
      };
      const predicted = [0, left, up, (left + up) >> 1, paeth()][filter ?? 0] ?? 0;
      line[i] = ((line[i] ?? 0) + predicted) & 0xff;
    }
    for (let alpha = 3; alpha < stride; alpha += BYTES) if (line[alpha] !== 0) return false;
    previous = line;
  }
  return width > 0 && height > 0;
}

describe('the config document', () => {
  it('takes its name from the identity function rather than spelling one', () => {
    expect(config.name).toBe(appIdentity(getEnv().environment).displayName);
  });

  /**
   * **The launcher name, as the OS shows it under the icon** — at the one environment this document
   * is evaluated at here, `jest.config.js`'s. The other three are `appIdentity.test.ts`'s.
   */
  it('names the app Rakieta development, at the environment it is evaluated at', () => {
    expect(getEnv().environment).toBe('development');
    expect(config.name).toBe('Rakieta development');
  });

  /**
   * ADR-0028 defers per-environment identifiers until a second backend exists to point
   * them at. Three installable apps that all reach the same laptop would be ceremony —
   * and the moment one exists, this assertion is the one that has to be argued with.
   * They are permanent from the first store submission (ADR-0211).
   */
  it('publishes exactly one bundle identifier, shared by both platforms', () => {
    expect(config.ios?.bundleIdentifier).toBe('com.rakieta.player');
    expect(config.android?.package).toBe('com.rakieta.player');
  });

  /** The Expo project — and so the development build's own scheme, `exp+rakieta-player://`. */
  it('is the Expo project rakieta-player', () => {
    expect(config.slug).toBe('rakieta-player');
  });

  it('publishes exactly one URL scheme, rakieta', () => {
    expect(config.scheme).toBe(APP_SCHEME);
    expect(config.scheme).toBe('rakieta');
  });

  /**
   * The web domain's links are the setting's, and **no domain is set** — here, as in every
   * environment today (#520). So the binary claims no associated domain and no verified intent
   * filter: a claim no site backs is a link that silently opens the browser. What a set domain
   * turns on is `appLinks.test.ts`'s, against the pure function this document spreads.
   */
  it('claims no web domain while none is set', () => {
    expect(config.ios?.associatedDomains).toBeUndefined();
    expect(config.android?.intentFilters).toBeUndefined();
  });

  /**
   * The two native capabilities onboarding needs, and the flag that decides what kind of
   * product this is.
   *
   * A **background** location is not a stronger version of a foreground one — it is a
   * movement trail, collected while the player is doing something else, and nobody agreed
   * to that. The ports never ask for it (`src/shared/lib/platform/location.test.ts`), and
   * this is the other half: the native project generated from this document does not even
   * declare the permission, so no later code could ask for one that the binary would
   * grant. Spelled out although `false` is already the plugin's default, because a
   * default is the kind of thing that gets flipped without anybody reading it.
   */
  it('asks for a foreground location and no background one, on either platform', () => {
    const [, options] = pluginNamed('expo-location');

    expect(options.isIosBackgroundLocationEnabled).toBe(false);
    expect(options.isAndroidBackgroundLocationEnabled).toBe(false);
    expect(options.isAndroidForegroundServiceEnabled).toBe(false);
  });

  /**
   * **Both uses, in the words the player reads before the OS asks** (ADR-0195 §3): the area,
   * and — when they say who's at a game — the check that they are at the club. A use the
   * prompt does not name is a use nobody agreed to.
   */
  it('names both uses of the location in its prompt', () => {
    const [, options] = pluginNamed('expo-location');

    expect(options.locationWhenInUsePermission).toBe(
      'Rakieta uses your location to set the area you play in and, when you say who’s at a game, to check you’re at the club.',
    );
  });

  /**
   * The prompt is the only place the app explains itself before the OS asks, and an
   * unexplained prompt is a prompt that gets refused. It names who is asking, too.
   */
  it('gives the photo-library prompt a reason to show the player', () => {
    const [, options] = pluginNamed('expo-image-picker');

    expect(options.photosPermission).toBe(
      'Rakieta uses your photos so you can put a picture of yourself on your profile.',
    );
  });

  /**
   * **The OS launch window is a plain night field with no icon, on both platforms** (ADR-0209 §1).
   * It cannot be removed — iOS requires a launch screen, and Android 12+ always draws one — so it is
   * the drawn splash's own edge colour, and the window and the splash read as one field from the tap:
   * no white, and no Expo logo. One colour and one image for both platforms and both appearances, so
   * no override (`ios`, `android`, `dark`) may paint anything else.
   */
  it('opens on a plain launch window in the splash’s edge colour, on both platforms', () => {
    const [, options] = pluginNamed('expo-splash-screen');

    expect(options.backgroundColor).toBe(theme.color.splashGroundEdge);
    expect(options.ios).toBeUndefined();
    expect(options.android).toBeUndefined();
    expect(options.dark).toBeUndefined();
  });

  /**
   * **No icon**: Android 12+ draws the launcher's icon on its system splash unless it is handed one,
   * so it is handed one with nothing in it. Read from the file, every pixel: an image with one
   * visible pixel is a logo.
   */
  it('hands the launch window an icon with nothing in it', () => {
    const [, options] = pluginNamed('expo-splash-screen');
    const image = readFileSync(join(__dirname, '../../..', String(options.image)));

    expect(String(options.image)).toMatch(/\.png$/);
    expect(everyPixelIsTransparent(image)).toBe(true);
  });

  /**
   * A secret in the native config is readable out of any shipped binary. `extra` carries
   * one key and it is the comment saying so; the environment name is deliberately *not*
   * mirrored here, so the badge and the HTTP client cannot read two different answers.
   */
  it('carries no config value in extra — only the note that nothing may go there', () => {
    expect(Object.keys(config.extra ?? {})).toEqual(['//']);
  });
});
