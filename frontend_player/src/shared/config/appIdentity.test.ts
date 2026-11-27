/**
 * The identity table, exercised at every environment — including the three that do not
 * run yet.
 *
 * That is the point of the ticket rather than a completeness ritual: with one backend
 * there is nothing to confuse today, and a configuration function nobody has ever
 * evaluated at `staging` is one that will be wrong the first time it matters. These
 * assertions are the exercise.
 *
 * Nothing here touches `loadEnv`, `getEnv` or `process.env` — `appIdentity` is a pure
 * function of its argument, which is why it is a module of its own.
 */

import { WORDMARK } from '@/shared/lib/bootstrap/domain/splashGeometry';

import {
  IDENTIFIED_ENVIRONMENTS,
  appIdentity,
  isAppEnvironment,
  type AppIdentity,
} from './appIdentity';
import { ENVIRONMENTS, type AppEnvironment } from './env';

/** The three the app is badged in. `production` is the exception, and is asserted alone. */
const BADGED: readonly AppEnvironment[] = ['local', 'development', 'staging'];

describe('the identity table', () => {
  it('covers exactly the four environments the app validates, in the same order', () => {
    expect(IDENTIFIED_ENVIRONMENTS).toEqual(ENVIRONMENTS);
  });

  it.each(ENVIRONMENTS)('answers for %s', (environment) => {
    const identity: AppIdentity = appIdentity(environment);

    expect(identity.displayName).not.toHaveLength(0);
  });
});

describe('the display name', () => {
  it('is the bare product name in production', () => {
    expect(appIdentity('production').displayName).toBe('Rakieta');
  });

  it.each(BADGED)('names the environment in %s', (environment) => {
    expect(appIdentity(environment).displayName).toBe(`Rakieta ${environment}`);
  });

  /**
   * **One spelling** (ADR-0211): the name under the icon is the word the splash draws a moment
   * later, so the launcher and the splash never disagree about which app this is.
   */
  it.each(ENVIRONMENTS)('starts with the word the splash draws, in %s', (environment) => {
    expect(appIdentity(environment).displayName.split(' ')[0]).toBe(WORDMARK.join(''));
  });

  it('is different in every environment, so the app switcher can never be ambiguous', () => {
    const names = ENVIRONMENTS.map((environment) => appIdentity(environment).displayName);

    expect(new Set(names).size).toBe(ENVIRONMENTS.length);
  });
});

describe('the badge', () => {
  /**
   * The one asymmetry in the table, and the one worth a test of its own: production is
   * visually clean, and a badge shipped to a player would be the failure this whole
   * mechanism is meant to make impossible.
   */
  it('is absent in production', () => {
    expect(appIdentity('production').badge).toBeNull();
  });

  it.each(BADGED)('is present in %s and names it', (environment) => {
    expect(appIdentity(environment).badge).toBe(environment.toUpperCase());
  });

  it('is absent in exactly one of the four', () => {
    const unbadged = ENVIRONMENTS.filter((environment) => appIdentity(environment).badge === null);

    expect(unbadged).toEqual(['production']);
  });
});

/**
 * `app.config.ts` reads a raw string out of `process.env`, where zod does not exist yet.
 * This is the narrowing that stands in for it.
 */
describe('narrowing a raw environment name', () => {
  it.each(ENVIRONMENTS)('accepts %s', (environment) => {
    expect(isAppEnvironment(environment)).toBe(true);
  });

  it.each([
    ['a missing variable', undefined],
    ['an empty string', ''],
    ['the old abbreviation', 'dev'],
    ['the other old abbreviation', 'prod'],
    ['a test environment that does not exist', 'test'],
    ['the right name, wrongly cased', 'Local'],
    ['a trailing space', 'local '],
    ['a non-string', 42],
  ])('refuses %s', (_case, value) => {
    expect(isAppEnvironment(value)).toBe(false);
  });

  /**
   * `'toString' in IDENTITIES` is true, so a narrowing written with `in` would accept
   * every method on Object's prototype as an environment name.
   */
  it('refuses a name inherited from Object.prototype', () => {
    expect(isAppEnvironment('toString')).toBe(false);
    expect(isAppEnvironment('constructor')).toBe(false);
  });
});
