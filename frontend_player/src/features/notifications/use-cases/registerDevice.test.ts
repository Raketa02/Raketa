/**
 * Telling the platform where one phone is, driven through the network boundary.
 *
 * Only `fetch` is faked, so the http client, its auth header, the mapper and the
 * request all run for real. The **OS** is a port here rather than the mocked
 * module, because these are the workflow's branches and each of them is a state
 * a real phone can be in — a build with no project id, a platform that is
 * neither store, three different settings — and a port makes each one a value
 * rather than a mock arrangement.
 */

import { refreshTokens } from '@/features/auth/types';
import { beginSession, clearStoredTokens, wireHttpCredentials } from '@/shared/lib/auth';
import type { DeviceKind, TimeSensitiveReading } from '@/shared/lib/notifications';
import { PUSH_DEVICE_PATH } from '@/test-support/notifications';
import { installTransport, noContent, type Transport } from '@/test-support/transport';

import { registerDevice, type DeviceReader } from './registerDevice';

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
  transport.on('PUT', PUSH_DEVICE_PATH, () => noContent());
});

afterEach(() => {
  transport.restore();
});

interface PhonePort extends DeviceReader {
  readonly calls: string[];
}

interface PhoneOptions {
  readonly platform?: DeviceKind | undefined;
  readonly token?: string | undefined;
  readonly timeSensitive?: TimeSensitiveReading;
}

/**
 * A phone, as the four things this workflow asks it.
 *
 * The two `in` checks are load-bearing: *no token* and *neither store* are two
 * of the three states this file exists to drive, and a destructuring default
 * would turn `{ token: undefined }` back into a phone that has one — which is
 * how three of these cases first passed against the opposite of what they say.
 */
function phone(options: PhoneOptions = {}): PhonePort {
  const platform = 'platform' in options ? options.platform : 'ios';
  const token = 'token' in options ? options.token : 'ExponentPushToken[abc]';
  const timeSensitive = options.timeSensitive ?? 'notSupported';
  const calls: string[] = [];
  return {
    calls,
    platform: () => {
      calls.push('platform');
      return platform;
    },
    pushToken: async () => {
      calls.push('pushToken');
      return token;
    },
    timeSensitive: async () => {
      calls.push('timeSensitive');
      return timeSensitive;
    },
    ensureChannel: async () => {
      calls.push('ensureChannel');
    },
  };
}

describe('registering one phone', () => {
  it('sends the token, the platform and the setting to PUT /api/v1/push/device', async () => {
    await registerDevice(phone({ platform: 'android', timeSensitive: 'disabled' }));

    expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)).toHaveLength(1);
    expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)[0]?.body).toEqual({
      token: 'ExponentPushToken[abc]',
      platform: 'android',
      time_sensitive_setting: 'disabled',
    });
  });

  /**
   * **All three settings reach the wire.** The value is read from the phone at
   * the moment of registering and carried; nothing folds `notSupported` into
   * `disabled`, which is the one distinction `ADR-0065` writes the fourth value
   * for.
   */
  it.each(['enabled', 'disabled', 'notSupported'] as const)(
    'reports %s as reported',
    async (setting) => {
      await registerDevice(phone({ timeSensitive: setting }));

      expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)[0]?.body).toMatchObject({
        time_sensitive_setting: setting,
      });
    },
  );

  /** The route is authenticated — a device belongs to a player, not to a handset. */
  it('carries her token', async () => {
    await registerDevice(phone());

    expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)[0]?.headers.Authorization).toBe(
      'Bearer access-1',
    );
  });

  /**
   * **`PUT`, because the address of one phone is a thing that is set.** The same
   * handset re-registers on every sign-in, every rotation and every settings
   * change, and a `POST` would make each of those a new device.
   */
  it('sets rather than creates', async () => {
    await registerDevice(phone());

    expect(transport.requests.map((request) => request.method)).toEqual(['PUT']);
  });

  /**
   * The channel has to exist before the server can address the phone, or a
   * message naming `offers` lands on Android's default channel instead — which
   * is `ADR-0065`'s one high-importance channel, silently downgraded.
   */
  it('creates the channel before telling the server where to send', async () => {
    const os = phone();
    await registerDevice(os);

    expect(os.calls).toContain('ensureChannel');
    expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)).toHaveLength(1);
  });

  it('answers what it registered', async () => {
    await expect(registerDevice(phone({ timeSensitive: 'enabled' }))).resolves.toEqual({
      token: 'ExponentPushToken[abc]',
      platform: 'ios',
      timeSensitive: 'enabled',
    });
  });
});

describe('the three ways there is nothing to register', () => {
  /**
   * The state every build is in until an Expo project id exists
   * (`Raketa02/Raketa#26`). It is a missing credential rather than a failure,
   * and there is nothing a player could do about it — so nothing is sent and
   * nothing is said.
   */
  it('sends nothing when the phone has no token to give', async () => {
    await expect(registerDevice(phone({ token: undefined }))).resolves.toBeUndefined();

    expect(transport.requests).toEqual([]);
  });

  it('sends nothing on a platform that is neither store', async () => {
    await expect(registerDevice(phone({ platform: undefined }))).resolves.toBeUndefined();

    expect(transport.requests).toEqual([]);
  });

  /** And it does not go looking for a token it has nowhere to send. */
  it('asks the phone nothing else once the platform is neither store', async () => {
    const os = phone({ platform: undefined });
    await registerDevice(os);

    expect(os.calls).toEqual(['platform']);
  });
});
