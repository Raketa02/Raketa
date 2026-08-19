import { ENVIRONMENTS, ConfigError, parseEnv, type AppEnvironment } from './env';

/** The only environment that runs today. */
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
    const apiUrl =
      environment === 'local' ? 'http://localhost:8000' : 'https://api.raketa.example';

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
 * The URL scheme is part of the contract, not a convention — and it is the **public-network**
 * form of the rule, because this URL is reached from a phone over the internet. The three
 * deployed environments must be `https://`; `local` may be either.
 *
 * `local` accepting `https://` is the correction #102 asked for: every tunnel a physical
 * device needs — `expo start --tunnel`, `cloudflared`, `tailscale funnel` — hands back an
 * `https://` address, so requiring `http://` refused the one case a tunnel exists for. See
 * docs/environments.md.
 *
 * Because no domain is registered yet, selecting a deployed environment today still fails at
 * launch: the only reachable backend is an `http://` one.
 */
describe('the per-environment URL scheme rule', () => {
  it('accepts an http:// LAN URL in local', () => {
    expect(parseEnv({ ...valid, EXPO_PUBLIC_API_URL: 'http://192.168.1.20:8000' })).toEqual({
      apiUrl: 'http://192.168.1.20:8000',
      environment: 'local',
    });
  });

  // The tunnel case. A phone that cannot reach the laptop's LAN IP is exactly why tunnels
  // exist, and all three of them are https — so `local` constrains the scheme no further
  // than "absolute http(s) URL".
  it('accepts an https:// tunnel URL in local', () => {
    expect(
      parseEnv({ ...valid, EXPO_PUBLIC_API_URL: 'https://sunny-otter.trycloudflare.example' }),
    ).toEqual({
      apiUrl: 'https://sunny-otter.trycloudflare.example',
      environment: 'local',
    });
  });

  it.each(DEPLOYED)('accepts an https:// URL in %s', (environment) => {
    expect(
      parseEnv({
        EXPO_PUBLIC_API_URL: 'https://api.raketa.example',
        EXPO_PUBLIC_ENV: environment,
      }),
    ).toEqual({ apiUrl: 'https://api.raketa.example', environment });
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
      parseEnv({ EXPO_PUBLIC_API_URL: 'ftp://api.raketa.example', EXPO_PUBLIC_ENV: environment }),
    ).toThrow(/EXPO_PUBLIC_API_URL/);
  });
});

/**
 * One typo, one complaint.
 *
 * A failing `.url()` or `.refine()` leaves zod's result *dirty* rather than aborting it, so
 * an object-level refinement still runs over the string the field just rejected. Before the
 * guard, `localhost:8000` under `production` produced two: "must start with http:// or
 * https://" **and** "must start with https:// when EXPO_PUBLIC_ENV is production". The
 * second is not what is wrong — the URL has no scheme at all, and being told about the
 * environment sends a reader looking in the wrong place.
 *
 * Counted rather than pattern-matched, because the defect is *an extra complaint*, and an
 * assertion that merely names the variable passes just as happily with two of them.
 */
describe('one complaint per typo', () => {
  const complaints = (raw: Parameters<typeof parseEnv>[0]): string[] => {
    try {
      parseEnv(raw);
    } catch (error) {
      return (error as ConfigError).message.split(';');
    }

    throw new Error('expected parseEnv to reject');
  };

  it.each(ENVIRONMENTS)('reports a scheme-less host:port once in %s', (environment) => {
    expect(
      complaints({ EXPO_PUBLIC_API_URL: 'localhost:8000', EXPO_PUBLIC_ENV: environment }),
    ).toHaveLength(1);
  });

  it.each(ENVIRONMENTS)('reports a non-HTTP scheme once in %s', (environment) => {
    expect(
      complaints({
        EXPO_PUBLIC_API_URL: 'ftp://api.raketa.example',
        EXPO_PUBLIC_ENV: environment,
      }),
    ).toHaveLength(1);
  });

  // A malformed URL is reported as a malformed URL, and the environment is not mentioned —
  // it is not the reason this value is wrong.
  it.each(ENVIRONMENTS)('does not blame the environment for a malformed URL in %s', (env) => {
    const [only] = complaints({ EXPO_PUBLIC_API_URL: 'localhost:8000', EXPO_PUBLIC_ENV: env });

    expect(only).toMatch(/must start with http:\/\/ or https:\/\//);
    expect(only).not.toContain('EXPO_PUBLIC_ENV');
  });

  // The rule itself still fires — this guard suppresses a duplicate, never the refusal.
  it('still reports a genuine scheme mismatch, once', () => {
    expect(
      complaints({ EXPO_PUBLIC_API_URL: 'http://localhost:8000', EXPO_PUBLIC_ENV: 'staging' }),
    ).toHaveLength(1);
  });
});
