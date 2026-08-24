/**
 * The one path in the app that fires the system dialog.
 *
 * What is asserted here is what happens **after** it closes, in both directions:
 * a grant registers the phone in the same breath, and a refusal does nothing at
 * all — no request, and nothing kept anywhere about the answer.
 */

import { refreshTokens } from '@/features/auth/types';
import { beginSession, clearStoredTokens, wireHttpCredentials } from '@/shared/lib/auth';
import type { NotificationStanding } from '@/shared/lib/notifications';
import { PUSH_DEVICE_PATH } from '@/test-support/notifications';
import { installTransport, noContent, type Transport } from '@/test-support/transport';

import { askForNotifications, type PermissionAsker } from './askForNotifications';

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

function phone(answer: NotificationStanding): PermissionAsker & { readonly asks: () => number } {
  let asks = 0;
  return {
    asks: () => asks,
    ask: async () => {
      asks += 1;
      return answer;
    },
    platform: () => 'ios',
    pushToken: async () => 'ExponentPushToken[abc]',
    timeSensitive: async () => 'notSupported',
    ensureChannel: async () => undefined,
  };
}

describe('spending the OS prompt', () => {
  it('registers the phone when the dialog was granted', async () => {
    const os = phone('granted');

    await expect(askForNotifications(os)).resolves.toBe('granted');

    expect(os.asks()).toBe(1);
    expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)).toHaveLength(1);
  });

  /**
   * The refusal costs her the message and nothing else (`ADR-0061`). There is
   * no *she said no* record on this client and no request that would create one
   * on the server: the OS holds that answer and is the only thing entitled to.
   */
  it('sends nothing at all when the dialog was refused', async () => {
    const os = phone('spent');

    await expect(askForNotifications(os)).resolves.toBe('spent');

    expect(os.asks()).toBe(1);
    expect(transport.requests).toEqual([]);
  });

  /**
   * The undetermined answer is the one a dialog leaves behind on Android after
   * one denial, where a second ask is still possible. It is not a grant, so
   * nothing is registered.
   */
  it('sends nothing when the dialog left the prompt unspent', async () => {
    await expect(askForNotifications(phone('askable'))).resolves.toBe('askable');

    expect(transport.requests).toEqual([]);
  });
});
