import { bootstrapApp, type BootstrapSteps } from './bootstrapApp';

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
      loadFonts: async () => {
        order.push('fonts');
      },
    });

    expect(order).toEqual(['config', 'managers', 'credentials', 'session', 'fonts']);
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
});
