import { loadEnv } from '@/shared/config/env';

import { bootstrapApp, sharedBootstrapSteps, type BootstrapSteps } from './bootstrapApp';

function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

/** Every step present and inert, so a test names only the one it is about. */
function steps(overrides: Partial<BootstrapSteps> = {}): BootstrapSteps {
  return {
    validateConfig: () => {},
    wirePlatformManagers: () => {},
    wireCredentials: () => {},
    restoreSession: async () => {},
    warmHome: () => {},
    readInstallReferrer: () => {},
    loadFonts: async () => {},
    ...overrides,
  };
}

describe('bootstrapApp', () => {
  it('does not resolve until the fonts have loaded', async () => {
    const fonts = deferred();
    let resolved = false;

    const run = bootstrapApp(steps({ loadFonts: () => fonts.promise })).then(() => {
      resolved = true;
    });

    await Promise.resolve();
    expect(resolved).toBe(false);

    fonts.resolve();
    await run;
    expect(resolved).toBe(true);
  });

  it('does not resolve until the session has been restored', async () => {
    // The step that decides which tree renders. Resolving before it lands is the
    // authenticated-tree flash the whole sequence exists to prevent.
    const session = deferred();
    let resolved = false;

    const run = bootstrapApp(steps({ restoreSession: () => session.promise })).then(() => {
      resolved = true;
    });

    await Promise.resolve();
    expect(resolved).toBe(false);

    session.resolve();
    await run;
    expect(resolved).toBe(true);
  });

  it('runs the sequence in the one documented order', async () => {
    const order: string[] = [];
    const record = (name: string) => () => {
      order.push(name);
    };

    await bootstrapApp({
      validateConfig: record('config'),
      wirePlatformManagers: record('managers'),
      wireCredentials: record('credentials'),
      restoreSession: async () => {
        order.push('session');
      },
      warmHome: record('home'),
      readInstallReferrer: record('referrer'),
      loadFonts: async () => {
        order.push('fonts');
      },
    });

    expect(order).toEqual([
      'config',
      'managers',
      'credentials',
      'session',
      'home',
      'referrer',
      'fonts',
    ]);
  });

  /**
   * The install referrer is another app's answer (#756): it is asked for at launch and held whenever
   * it comes, so the splash never waits on Google Play — the step starts it and returns.
   */
  it('starts the install referrer’s read without waiting for it', async () => {
    // Google Play never answers here: a sequence that awaited the step would never resolve.
    const play = deferred();
    let asked = false;
    let resolved = false;

    const run = bootstrapApp(
      steps({
        readInstallReferrer: () => {
          asked = true;
          return play.promise;
        },
      }),
    ).then(() => {
      resolved = true;
    });

    await run;
    expect(asked).toBe(true);
    expect(resolved).toBe(true);
    play.resolve();
  });

  /**
   * **Home's reads set out while the splash plays** (#874; ADR-0209 §2, amended 2026-11-24): the step
   * is started once the session is restored — the account it decides from is cached by then — and the
   * sequence never waits for it, so the splash is held by nothing a read does.
   */
  it('starts warming Home once the session is restored, and never waits for it', async () => {
    const session = deferred();
    const reads = deferred();
    let warmed = false;
    let resolved = false;

    const run = bootstrapApp(
      steps({
        restoreSession: () => session.promise,
        warmHome: () => {
          warmed = true;
          return reads.promise;
        },
      }),
    ).then(() => {
      resolved = true;
    });

    await Promise.resolve();
    expect(warmed).toBe(false);

    session.resolve();
    // Home's reads never land here: a sequence that awaited the step would never resolve.
    await run;
    expect(warmed).toBe(true);
    expect(resolved).toBe(true);
    reads.resolve();
  });

  it('fails when the config does, without spending a launch on anything else', async () => {
    const loadFonts = jest.fn(async () => {});
    const restoreSession = jest.fn(async () => {});

    await expect(
      bootstrapApp(
        steps({
          validateConfig: () => {
            throw new Error('EXPO_PUBLIC_API_URL: Required');
          },
          loadFonts,
          restoreSession,
        }),
      ),
    ).rejects.toThrow('EXPO_PUBLIC_API_URL: Required');

    expect(restoreSession).not.toHaveBeenCalled();
    expect(loadFonts).not.toHaveBeenCalled();
  });

  it('hands the HTTP client its credentials before the session is restored', async () => {
    // The validation call is authenticated. Restoring before wiring would send it with
    // no Authorization header and read the 401 as "this session is over".
    const order: string[] = [];

    await bootstrapApp(
      steps({
        wireCredentials: () => {
          order.push('credentials');
        },
        restoreSession: async () => {
          order.push('session');
        },
      }),
    );

    expect(order).toEqual(['credentials', 'session']);
  });

  // The order test above passes for any `validateConfig`, including one that only *reads*
  // config. `loadEnv` is the function that parses; `getEnv` is the lazy read that throws
  // only once somebody asks. Wiring the second is how eager validation becomes lazy
  // validation without a single test noticing.
  it('validates the config eagerly rather than reading it lazily', () => {
    expect(sharedBootstrapSteps.validateConfig).toBe(loadEnv);
  });
});
