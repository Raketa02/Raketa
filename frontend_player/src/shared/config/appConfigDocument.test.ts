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

import appConfig from '../../../app.config';

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

describe('the config document', () => {
  it('takes its name from the identity function rather than spelling one', () => {
    expect(config.name).toBe(appIdentity(getEnv().environment).displayName);
  });

  /**
   * ADR-0028 defers per-environment identifiers until a second backend exists to point
   * them at. Three installable apps that all reach the same laptop would be ceremony —
   * and the moment one exists, this assertion is the one that has to be argued with.
   */
  it('publishes exactly one bundle identifier, shared by both platforms', () => {
    expect(config.ios?.bundleIdentifier).toBe('com.raketa.player');
    expect(config.android?.package).toBe('com.raketa.player');
  });

  it('publishes exactly one URL scheme', () => {
    expect(config.scheme).toBe(APP_SCHEME);
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
      'Raketa uses your location to set the area you play in and, when you say who’s at a game, to check you’re at the club.',
    );
  });

  /**
   * The prompt is the only place the app explains itself before the OS asks, and an
   * unexplained prompt is a prompt that gets refused.
   */
  it('gives the photo-library prompt a reason to show the player', () => {
    const [, options] = pluginNamed('expo-image-picker');

    expect(options.photosPermission).toEqual(expect.any(String));
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
