import { ENVIRONMENTS, ConfigError, parseEnv, type AppEnvironment } from './env';

/** The only environment that runs today. */
const valid = {
  EXPO_PUBLIC_API_URL: 'http://localhost:8000',
  EXPO_PUBLIC_FEATURES_URL: 'http://localhost:3040',
  EXPO_PUBLIC_ENV: 'local',
} as const;

/** Where a deployed environment's datafiles would be served — an https bucket, never a laptop. */
const DEPLOYED_FEATURES_URL = 'https://features.raketa.example';

/** The three deployed environments. None is provisioned — no domain is registered yet. */
const DEPLOYED: readonly AppEnvironment[] = ['development', 'staging', 'production'];

/** A raw environment that passes in `environment`, for the cases that break one field of it. */
function wellFormedFor(environment: AppEnvironment) {
  return environment === 'local'
    ? valid
    : {
        EXPO_PUBLIC_API_URL: 'https://api.raketa.example',
        EXPO_PUBLIC_FEATURES_URL: DEPLOYED_FEATURES_URL,
        EXPO_PUBLIC_ENV: environment,
      };
}

describe('parseEnv', () => {
  it('maps a valid environment onto the app config', () => {
    expect(parseEnv(valid)).toEqual({
      apiUrl: 'http://localhost:8000',
      featuresUrl: 'http://localhost:3040',
      environment: 'local',
      linkDomain: null,
    });
  });

  it('rejects a missing API URL and names the variable', () => {
    const { EXPO_PUBLIC_API_URL: _omitted, ...rest } = valid;

    expect(() => parseEnv(rest)).toThrow(ConfigError);
    expect(() => parseEnv(rest)).toThrow(/EXPO_PUBLIC_API_URL/);
  });

  // The datafile's base. Required rather than optional, like the API URL beside it: a build
  // with no flags host would run on code defaults for ever and nothing would say so — which is
  // the one silent failure ADR-0180 names as the cost of two repositories agreeing.
  it('rejects a missing features URL and names the variable', () => {
    const { EXPO_PUBLIC_FEATURES_URL: _omitted, ...rest } = valid;

    expect(() => parseEnv(rest)).toThrow(ConfigError);
    expect(() => parseEnv(rest)).toThrow(/EXPO_PUBLIC_FEATURES_URL/);
  });

  it('rejects a features URL that is not a URL', () => {
    expect(() => parseEnv({ ...valid, EXPO_PUBLIC_FEATURES_URL: 'nonsense' })).toThrow(
      /EXPO_PUBLIC_FEATURES_URL/,
    );
  });

  it('rejects an API URL that is not a URL', () => {
    expect(() => parseEnv({ ...valid, EXPO_PUBLIC_API_URL: 'nonsense' })).toThrow(
      /EXPO_PUBLIC_API_URL/,
    );
  });

  it('never puts a config value in the failure message', () => {
    const secretish = 'https://user:hunter2@api.example.com';

    try {
      parseEnv({
        EXPO_PUBLIC_API_URL: secretish,
        EXPO_PUBLIC_FEATURES_URL: secretish,
        EXPO_PUBLIC_ENV: 'kittens',
      });
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
    const apiUrl = environment === 'local' ? 'http://localhost:8000' : 'https://api.raketa.example';
    const featuresUrl = environment === 'local' ? 'http://localhost:3040' : DEPLOYED_FEATURES_URL;

    expect(
      parseEnv({
        EXPO_PUBLIC_API_URL: apiUrl,
        EXPO_PUBLIC_FEATURES_URL: featuresUrl,
        EXPO_PUBLIC_ENV: environment,
      }),
    ).toEqual({ apiUrl, featuresUrl, environment, linkDomain: null });
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
    const { EXPO_PUBLIC_ENV: _omitted, ...rest } = valid;

    expect(() => parseEnv(rest)).toThrow(/EXPO_PUBLIC_ENV/);
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
      featuresUrl: 'http://localhost:3040',
      environment: 'local',
      linkDomain: null,
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
      featuresUrl: 'http://localhost:3040',
      environment: 'local',
      linkDomain: null,
    });
  });

  it.each(DEPLOYED)('accepts an https:// URL in %s', (environment) => {
    expect(
      parseEnv({
        EXPO_PUBLIC_API_URL: 'https://api.raketa.example',
        EXPO_PUBLIC_FEATURES_URL: DEPLOYED_FEATURES_URL,
        EXPO_PUBLIC_ENV: environment,
      }),
    ).toEqual({
      apiUrl: 'https://api.raketa.example',
      featuresUrl: DEPLOYED_FEATURES_URL,
      environment,
      linkDomain: null,
    });
  });

  it.each(DEPLOYED)('rejects an http:// URL in %s', (environment) => {
    expect(() =>
      parseEnv({
        EXPO_PUBLIC_API_URL: 'http://localhost:8000',
        EXPO_PUBLIC_FEATURES_URL: DEPLOYED_FEATURES_URL,
        EXPO_PUBLIC_ENV: environment,
      }),
    ).toThrow(ConfigError);
  });

  // The whole point of the rule today: a laptop URL under a deployed name is the mistake
  // that would otherwise ship a build pointing at nothing.
  it('names both variables when the scheme and the environment disagree', () => {
    try {
      parseEnv({
        EXPO_PUBLIC_API_URL: 'http://localhost:8000',
        EXPO_PUBLIC_FEATURES_URL: DEPLOYED_FEATURES_URL,
        EXPO_PUBLIC_ENV: 'production',
      });
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
      parseEnv({
        EXPO_PUBLIC_API_URL: secretish,
        EXPO_PUBLIC_FEATURES_URL: DEPLOYED_FEATURES_URL,
        EXPO_PUBLIC_ENV: 'staging',
      });
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
      parseEnv({ ...wellFormedFor(environment), EXPO_PUBLIC_API_URL: 'localhost:8000' }),
    ).toThrow(/EXPO_PUBLIC_API_URL/);
  });

  it.each(ENVIRONMENTS)('rejects a scheme that is neither http nor https in %s', (environment) => {
    expect(() =>
      parseEnv({ ...wellFormedFor(environment), EXPO_PUBLIC_API_URL: 'ftp://api.raketa.example' }),
    ).toThrow(/EXPO_PUBLIC_API_URL/);
  });
});

/**
 * **The datafile's URL obeys the same rule, and for the same reason**
 * ([ADR-0180](../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §4). It is fetched from a phone over the internet exactly as the API is, and a datafile read in
 * the clear is one somebody on the café Wi-Fi can rewrite — which turns a screen off, or on, for
 * one player. Plain `http` is `local`'s alone: today that is the Mac's LAN address, served by the
 * flags repo's own script.
 */
describe('the features URL', () => {
  it('accepts the Mac on the LAN over http:// in local', () => {
    expect(
      parseEnv({ ...valid, EXPO_PUBLIC_FEATURES_URL: 'http://192.168.0.204:3040' }).featuresUrl,
    ).toBe('http://192.168.0.204:3040');
  });

  it.each(DEPLOYED)('rejects an http:// features URL in %s, naming both variables', (env) => {
    try {
      parseEnv({
        EXPO_PUBLIC_API_URL: 'https://api.raketa.example',
        EXPO_PUBLIC_FEATURES_URL: 'http://192.168.0.204:3040',
        EXPO_PUBLIC_ENV: env,
      });
      throw new Error('expected parseEnv to reject');
    } catch (error) {
      expect(error).toBeInstanceOf(ConfigError);
      expect((error as ConfigError).message).toMatch(/EXPO_PUBLIC_FEATURES_URL: must start with/);
      expect((error as ConfigError).message).toMatch(/EXPO_PUBLIC_ENV/);
      // The API URL is fine, and the refusal does not say otherwise.
      expect((error as ConfigError).message).not.toMatch(/EXPO_PUBLIC_API_URL/);
    }
  });

  it.each(ENVIRONMENTS)('rejects a host:port with no scheme in %s', (environment) => {
    expect(() =>
      parseEnv({ ...wellFormedFor(environment), EXPO_PUBLIC_FEATURES_URL: 'localhost:3040' }),
    ).toThrow(/EXPO_PUBLIC_FEATURES_URL/);
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
      complaints({ ...wellFormedFor(environment), EXPO_PUBLIC_API_URL: 'localhost:8000' }),
    ).toHaveLength(1);
  });

  it.each(ENVIRONMENTS)('reports a non-HTTP scheme once in %s', (environment) => {
    expect(
      complaints({
        ...wellFormedFor(environment),
        EXPO_PUBLIC_API_URL: 'ftp://api.raketa.example',
      }),
    ).toHaveLength(1);
  });

  // A malformed URL is reported as a malformed URL, and the environment is not mentioned —
  // it is not the reason this value is wrong.
  it.each(ENVIRONMENTS)('does not blame the environment for a malformed URL in %s', (env) => {
    const [only] = complaints({ ...wellFormedFor(env), EXPO_PUBLIC_API_URL: 'localhost:8000' });

    expect(only).toMatch(/must start with http:\/\/ or https:\/\//);
    expect(only).not.toContain('EXPO_PUBLIC_ENV');
  });

  // The same guard, on the second URL: one rule written twice would be two guards, and the
  // second is the one that gets forgotten.
  it.each(ENVIRONMENTS)('reports a scheme-less features URL once in %s', (environment) => {
    const found = complaints({
      ...wellFormedFor(environment),
      EXPO_PUBLIC_FEATURES_URL: 'localhost:3040',
    });

    expect(found).toHaveLength(1);
    expect(found[0]).not.toContain('EXPO_PUBLIC_ENV');
  });

  // The rule itself still fires — this guard suppresses a duplicate, never the refusal.
  it('still reports a genuine scheme mismatch, once', () => {
    expect(
      complaints({ ...wellFormedFor('staging'), EXPO_PUBLIC_API_URL: 'http://localhost:8000' }),
    ).toHaveLength(1);
  });

  // Two URLs in the clear under a deployed name are two mistakes, and each is named once.
  it('reports each URL that breaks the scheme rule, once each', () => {
    expect(
      complaints({
        EXPO_PUBLIC_API_URL: 'http://localhost:8000',
        EXPO_PUBLIC_FEATURES_URL: 'http://localhost:3040',
        EXPO_PUBLIC_ENV: 'staging',
      }),
    ).toHaveLength(2);
  });
});

/**
 * **The web domain the app's links live on** — optional, and unset in every environment today
 * (#520, ADR-0187 §7). The native project reads the same variable through the same function
 * (`appLinks.ts`), so the running app and the binary agree about which links are the app's.
 */
describe('the link domain', () => {
  it('is absent while nothing is set, and while it is set to nothing', () => {
    expect(parseEnv(valid).linkDomain).toBeNull();
    expect(parseEnv({ ...valid, EXPO_PUBLIC_LINK_DOMAIN: '' }).linkDomain).toBeNull();
  });

  it('is the host once one is set, in any environment', () => {
    expect(parseEnv({ ...valid, EXPO_PUBLIC_LINK_DOMAIN: 'raketa.app' }).linkDomain).toBe(
      'raketa.app',
    );
    expect(
      parseEnv({ ...wellFormedFor('production'), EXPO_PUBLIC_LINK_DOMAIN: 'raketa.app' })
        .linkDomain,
    ).toBe('raketa.app');
  });

  it('refuses a URL where a host belongs, naming the variable and not the value', () => {
    const typed = 'https://links.hunter2.example/join';

    expect(() => parseEnv({ ...valid, EXPO_PUBLIC_LINK_DOMAIN: typed })).toThrow(
      /EXPO_PUBLIC_LINK_DOMAIN/,
    );
    try {
      parseEnv({ ...valid, EXPO_PUBLIC_LINK_DOMAIN: typed });
    } catch (error) {
      expect((error as ConfigError).message).not.toContain('hunter2');
    }
  });
});
