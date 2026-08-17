import { ENVIRONMENTS, ConfigError, parseEnv, type AppEnvironment } from './env';

/** The only environment that runs today, and the only one an `http://` URL is legal in. */
const valid = {
  EXPO_PUBLIC_API_URL: 'http://localhost:8000',
  EXPO_PUBLIC_ENV: 'local',
} as const;

/** The three deployed environments. None is provisioned — no domain is registered yet. */
const DEPLOYED: readonly AppEnvironment[] = ['development', 'staging', 'production'];

describe('parseEnv', () => {
  it('maps a valid environment onto the app config', () => {
    expect(parseEnv(valid)).toEqual({
      apiUrl: 'http://localhost:8000',
      environment: 'local',
    });
  });

  it('rejects a missing API URL and names the variable', () => {
    expect(() => parseEnv({ EXPO_PUBLIC_ENV: 'local' })).toThrow(ConfigError);
    expect(() => parseEnv({ EXPO_PUBLIC_ENV: 'local' })).toThrow(/EXPO_PUBLIC_API_URL/);
  });

  it('rejects an API URL that is not a URL', () => {
    expect(() => parseEnv({ ...valid, EXPO_PUBLIC_API_URL: 'nonsense' })).toThrow(
      /EXPO_PUBLIC_API_URL/,
    );
  });

  it('never puts a config value in the failure message', () => {
    const secretish = 'https://user:hunter2@api.example.com';

    try {
      parseEnv({ EXPO_PUBLIC_API_URL: secretish, EXPO_PUBLIC_ENV: 'kittens' });
      throw new Error('expected parseEnv to reject');
    } catch (error) {
      expect(error).toBeInstanceOf(ConfigError);
      expect((error as ConfigError).message).not.toContain('hunter2');
      expect((error as ConfigError).message).not.toContain(secretish);
    }
  });
});

/**
 * The four names are the same four the backend and the club app use. A fifth spelling
 * here would mean the three apps disagree about where they are running, which is the
 * failure the shared vocabulary exists to remove.
 */
describe('the environment names', () => {
  it('is exactly the four, in the order the platform spells them', () => {
    expect(ENVIRONMENTS).toEqual(['local', 'development', 'staging', 'production']);
  });

  it.each(ENVIRONMENTS)('accepts %s', (environment) => {
    const apiUrl = environment === 'local' ? 'http://localhost:8000' : 'https://api.rakieta.app';

    expect(parseEnv({ EXPO_PUBLIC_API_URL: apiUrl, EXPO_PUBLIC_ENV: environment })).toEqual({
      apiUrl,
      environment,
    });
  });

  // `dev` and `prod` are the spellings the backend used to accept and no longer does;
  // `test` is the fifth name that was deliberately never introduced — a test run happens
  // on a laptop or a CI runner, both of which are `local`.
  it.each(['dev', 'prod', 'production ', 'Local', 'test', ''])(
    'rejects %p and names the variable',
    (environment) => {
      expect(() => parseEnv({ ...valid, EXPO_PUBLIC_ENV: environment })).toThrow(ConfigError);
      expect(() => parseEnv({ ...valid, EXPO_PUBLIC_ENV: environment })).toThrow(/EXPO_PUBLIC_ENV/);
    },
  );

  it('rejects a missing environment and names the variable', () => {
    expect(() => parseEnv({ EXPO_PUBLIC_API_URL: 'http://localhost:8000' })).toThrow(
      /EXPO_PUBLIC_ENV/,
    );
  });

  // zod's own `invalid_enum_value` message ends `received '…'`. Config lands in logs and
  // crash reports, so the schema replaces that message rather than echoing what it read.
  it('does not echo the rejected name back', () => {
    try {
      parseEnv({ ...valid, EXPO_PUBLIC_ENV: 'kittens' });
      throw new Error('expected parseEnv to reject');
    } catch (error) {
      expect((error as ConfigError).message).not.toContain('kittens');
    }
  });
});

/**
 * The URL scheme is part of the contract, not a convention. `local` is a laptop, a LAN IP
 * or a tunnel; the other three are deployed and are reached over TLS. Because no domain is
 * registered yet, selecting a deployed environment today fails at launch saying so — which
 * is the truth, and is better than silently pointing somewhere wrong.
 */
describe('the per-environment URL scheme rule', () => {
  it('accepts an http:// URL in local', () => {
    expect(parseEnv({ ...valid, EXPO_PUBLIC_API_URL: 'http://192.168.1.20:8000' })).toEqual({
      apiUrl: 'http://192.168.1.20:8000',
      environment: 'local',
    });
  });

  it('rejects an https:// URL in local', () => {
    expect(() => parseEnv({ ...valid, EXPO_PUBLIC_API_URL: 'https://api.rakieta.app' })).toThrow(
      ConfigError,
    );
  });

  it.each(DEPLOYED)('accepts an https:// URL in %s', (environment) => {
    expect(
      parseEnv({ EXPO_PUBLIC_API_URL: 'https://api.rakieta.app', EXPO_PUBLIC_ENV: environment }),
    ).toEqual({ apiUrl: 'https://api.rakieta.app', environment });
  });

  it.each(DEPLOYED)('rejects an http:// URL in %s', (environment) => {
    expect(() =>
      parseEnv({ EXPO_PUBLIC_API_URL: 'http://localhost:8000', EXPO_PUBLIC_ENV: environment }),
    ).toThrow(ConfigError);
  });

  // The whole point of the rule today: a laptop URL under a deployed name is the mistake
  // that would otherwise ship a build pointing at nothing.
  it('names both variables when the scheme and the environment disagree', () => {
    try {
      parseEnv({ EXPO_PUBLIC_API_URL: 'http://localhost:8000', EXPO_PUBLIC_ENV: 'production' });
      throw new Error('expected parseEnv to reject');
    } catch (error) {
      expect(error).toBeInstanceOf(ConfigError);
      expect((error as ConfigError).message).toMatch(/EXPO_PUBLIC_API_URL/);
      expect((error as ConfigError).message).toMatch(/EXPO_PUBLIC_ENV/);
      expect((error as ConfigError).message).toMatch(/https:\/\//);
    }
  });

  it('never puts the URL in a scheme-mismatch message', () => {
    const secretish = 'http://user:hunter2@10.0.0.5:8000';

    try {
      parseEnv({ EXPO_PUBLIC_API_URL: secretish, EXPO_PUBLIC_ENV: 'staging' });
      throw new Error('expected parseEnv to reject');
    } catch (error) {
      expect((error as ConfigError).message).not.toContain('hunter2');
      expect((error as ConfigError).message).not.toContain(secretish);
    }
  });

  // WHATWG parsing reads this as the protocol `localhost:` and calls it a valid URL. It
  // is the value a developer actually mistypes, so it has to be rejected by name — and in
  // every environment, not only the one the fixture happens to use.
  it.each(ENVIRONMENTS)('rejects a host:port with no scheme in %s', (environment) => {
    expect(() =>
      parseEnv({ EXPO_PUBLIC_API_URL: 'localhost:8000', EXPO_PUBLIC_ENV: environment }),
    ).toThrow(/EXPO_PUBLIC_API_URL/);
  });

  it.each(ENVIRONMENTS)('rejects a scheme that is neither http nor https in %s', (environment) => {
    expect(() =>
      parseEnv({ EXPO_PUBLIC_API_URL: 'ftp://api.rakieta.app', EXPO_PUBLIC_ENV: environment }),
    ).toThrow(/EXPO_PUBLIC_API_URL/);
  });
});
