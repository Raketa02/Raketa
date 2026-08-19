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
    expect(config.scheme).toBe('raketa');
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
