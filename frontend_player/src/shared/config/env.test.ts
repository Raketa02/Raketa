import { ConfigError, parseEnv } from './env';

const valid = {
  EXPO_PUBLIC_API_URL: 'http://localhost:8000',
  EXPO_PUBLIC_ENV: 'development',
} as const;

describe('parseEnv', () => {
  it('maps a valid environment onto the app config', () => {
    expect(parseEnv(valid)).toEqual({
      apiUrl: 'http://localhost:8000',
      environment: 'development',
    });
  });

  it('rejects a missing API URL and names the variable', () => {
    expect(() => parseEnv({ EXPO_PUBLIC_ENV: 'development' })).toThrow(ConfigError);
    expect(() => parseEnv({ EXPO_PUBLIC_ENV: 'development' })).toThrow(/EXPO_PUBLIC_API_URL/);
  });

  it('accepts an https API URL', () => {
    expect(parseEnv({ ...valid, EXPO_PUBLIC_API_URL: 'https://api.rakieta.app' })).toEqual({
      apiUrl: 'https://api.rakieta.app',
      environment: 'development',
    });
  });

  it('rejects an API URL that is not a URL', () => {
    expect(() => parseEnv({ ...valid, EXPO_PUBLIC_API_URL: 'nonsense' })).toThrow(
      /EXPO_PUBLIC_API_URL/,
    );
  });

  // WHATWG parsing reads this as the protocol `localhost:` and calls it a valid URL. It
  // is the value a developer actually mistypes, so it has to be rejected by name.
  it('rejects a host:port with no scheme', () => {
    expect(() => parseEnv({ ...valid, EXPO_PUBLIC_API_URL: 'localhost:8000' })).toThrow(
      /EXPO_PUBLIC_API_URL/,
    );
  });

  it('rejects an unknown environment name', () => {
    expect(() => parseEnv({ ...valid, EXPO_PUBLIC_ENV: 'prod' })).toThrow(/EXPO_PUBLIC_ENV/);
  });

  it('never puts a config value in the failure message', () => {
    const secretish = 'https://user:hunter2@api.example.com';

    try {
      parseEnv({ EXPO_PUBLIC_API_URL: secretish, EXPO_PUBLIC_ENV: 'prod' });
      throw new Error('expected parseEnv to reject');
    } catch (error) {
      expect(error).toBeInstanceOf(ConfigError);
      expect((error as ConfigError).message).not.toContain('hunter2');
      expect((error as ConfigError).message).not.toContain(secretish);
    }
  });
});
