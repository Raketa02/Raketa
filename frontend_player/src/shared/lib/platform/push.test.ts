/**
 * The push port's own readings of `expo-notifications` (#559): which phone may ask for a token at
 * all, a token kept until the system replaces it, the permission in the platform's words, and a
 * tapped push handed over once — the cold start's among them.
 *
 * The library is jest's mock of it here (`jest.setup.js`), so what can be proved is what this file
 * decides, never what Expo does. The build's push switches (`shared/config/push.ts`) are swapped per
 * case by loading the port afresh under each.
 */

import { Platform } from 'react-native';

import { TIMEOUT_MS } from '@/shared/lib/http';

import type { PushPort } from './push';

interface Notifications {
  readonly DEFAULT_ACTION_IDENTIFIER: string;
  readonly getPermissionsAsync: jest.Mock;
  readonly requestPermissionsAsync: jest.Mock;
  readonly setNotificationChannelAsync: jest.Mock;
  readonly getExpoPushTokenAsync: jest.Mock;
  readonly addPushTokenListener: jest.Mock;
  readonly addNotificationReceivedListener: jest.Mock;
  readonly addNotificationResponseReceivedListener: jest.Mock;
  readonly getLastNotificationResponseAsync: jest.Mock;
}

const notifications = jest.requireMock<Notifications>('expo-notifications');

/** The port, loaded afresh under these switches — its kept token and its taps start empty. */
function portWith(config: { projectId: string | null; iphonePush: boolean }): PushPort {
  let port: PushPort | undefined;
  jest.isolateModules(() => {
    jest.doMock('@/shared/config/push', () => ({
      EXPO_PROJECT_ID: config.projectId,
      IPHONE_PUSH: config.iphonePush,
      PUSH_PROJECT: {},
    }));
    port = (require('./push') as typeof import('./push')).devicePush;
  });
  return port!;
}

/** A tap on a push's body, as the library reports one. */
function tapOn(
  identifier: string,
  data: unknown,
  action = notifications.DEFAULT_ACTION_IDENTIFIER,
) {
  return {
    actionIdentifier: action,
    notification: { date: 0, request: { identifier, content: { title: 't', body: 'b', data } } },
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  notifications.getExpoPushTokenAsync.mockImplementation(async () => ({
    type: 'expo',
    data: 'ExponentPushToken[abc]',
  }));
});

afterEach(() => jest.restoreAllMocks());

describe('which phone may ask for a token', () => {
  it('none at all while there is no Expo project — and Expo is never asked', async () => {
    const port = portWith({ projectId: null, iphonePush: true });

    expect(await port.readToken()).toBeNull();
    expect(notifications.getExpoPushTokenAsync).not.toHaveBeenCalled();
  });

  it('no iPhone without the push entitlement', async () => {
    jest.replaceProperty(Platform, 'OS', 'ios');
    const port = portWith({ projectId: 'project-1', iphonePush: false });

    expect(await port.readToken()).toBeNull();
    expect(notifications.getExpoPushTokenAsync).not.toHaveBeenCalled();
  });

  it('an Android phone once a project exists — minted for that project', async () => {
    jest.replaceProperty(Platform, 'OS', 'android');
    const port = portWith({ projectId: 'project-1', iphonePush: false });

    expect(await port.readToken()).toBe('ExponentPushToken[abc]');
    expect(notifications.getExpoPushTokenAsync).toHaveBeenCalledWith({ projectId: 'project-1' });
  });

  it('none, and no rejection, when Expo cannot be reached', async () => {
    jest.replaceProperty(Platform, 'OS', 'android');
    notifications.getExpoPushTokenAsync.mockRejectedValue(new Error('offline'));
    const port = portWith({ projectId: 'project-1', iphonePush: true });

    await expect(port.readToken()).resolves.toBeNull();
  });
});

describe('a token is never waited on for ever', () => {
  it('is none once the app’s request timeout has passed without Expo answering', async () => {
    jest.useFakeTimers();
    try {
      jest.replaceProperty(Platform, 'OS', 'android');
      notifications.getExpoPushTokenAsync.mockImplementation(() => new Promise(() => {}));
      const port = portWith({ projectId: 'project-1', iphonePush: true });

      const reading = port.readToken();
      jest.advanceTimersByTime(TIMEOUT_MS.request);

      await expect(reading).resolves.toBeNull();
    } finally {
      jest.useRealTimers();
    }
  });
});

describe('a token is kept until the system replaces it', () => {
  it('is minted once, and again after the system says it changed', async () => {
    jest.replaceProperty(Platform, 'OS', 'android');
    const port = portWith({ projectId: 'project-1', iphonePush: true });
    const changed = jest.fn();
    port.onTokenChange(changed);

    await port.readToken();
    await port.readToken();
    expect(notifications.getExpoPushTokenAsync).toHaveBeenCalledTimes(1);

    const replaced = notifications.addPushTokenListener.mock.calls[0]![0] as () => void;
    replaced();
    expect(changed).toHaveBeenCalledTimes(1);

    await port.readToken();
    expect(notifications.getExpoPushTokenAsync).toHaveBeenCalledTimes(2);
  });

  it('is not kept while it could not be had — the next read asks again', async () => {
    jest.replaceProperty(Platform, 'OS', 'android');
    notifications.getExpoPushTokenAsync.mockRejectedValueOnce(new Error('offline'));
    const port = portWith({ projectId: 'project-1', iphonePush: true });

    expect(await port.readToken()).toBeNull();
    expect(await port.readToken()).toBe('ExponentPushToken[abc]');
  });
});

describe('the permission', () => {
  it('is read in the platform’s words', async () => {
    const port = portWith({ projectId: null, iphonePush: false });
    notifications.getPermissionsAsync.mockResolvedValueOnce({
      granted: false,
      canAskAgain: false,
      status: 'denied',
    });

    expect(await port.getPermission()).toBe('blocked');
  });

  it('asks through a channel on Android, made before the question', async () => {
    jest.replaceProperty(Platform, 'OS', 'android');
    const port = portWith({ projectId: null, iphonePush: false });

    expect(await port.requestPermission()).toBe('granted');
    expect(notifications.setNotificationChannelAsync).toHaveBeenCalledWith(
      'default',
      expect.objectContaining({ name: 'Your games' }),
    );
    expect(notifications.setNotificationChannelAsync.mock.invocationCallOrder[0]).toBeLessThan(
      notifications.requestPermissionsAsync.mock.invocationCallOrder[0]!,
    );
  });

  it('makes no channel on an iPhone', async () => {
    jest.replaceProperty(Platform, 'OS', 'ios');
    const port = portWith({ projectId: null, iphonePush: false });

    await port.requestPermission();
    expect(notifications.setNotificationChannelAsync).not.toHaveBeenCalled();
  });
});

describe('a push while the app is open', () => {
  it('is handed up with its words and what it carried, unread', () => {
    const port = portWith({ projectId: null, iphonePush: false });
    const heard = jest.fn();
    port.onNotice(heard);

    const arrived = notifications.addNotificationReceivedListener.mock.calls[0]![0] as (
      notification: unknown,
    ) => void;
    arrived(tapOn('n-1', { opens: 'BOOKING' }).notification);

    expect(heard).toHaveBeenCalledWith({ title: 't', body: 'b', data: { opens: 'BOOKING' } });
  });
});

describe('a push tapped', () => {
  it('hands over the cold start’s tap, once, to the first listener', async () => {
    notifications.getLastNotificationResponseAsync.mockResolvedValue(tapOn('n-1', { a: 1 }));
    const port = portWith({ projectId: null, iphonePush: false });
    const first = jest.fn();
    const second = jest.fn();

    port.onOpen(first);
    await Promise.resolve();
    await Promise.resolve();
    port.onOpen(second);
    await Promise.resolve();
    await Promise.resolve();

    expect(first).toHaveBeenCalledWith({ a: 1 });
    expect(second).not.toHaveBeenCalled();
  });

  it('hands a tap over once, however many ways it arrives', async () => {
    const port = portWith({ projectId: null, iphonePush: false });
    const opened = jest.fn();
    port.onOpen(opened);
    const tapped = notifications.addNotificationResponseReceivedListener.mock.calls[0]![0] as (
      response: unknown,
    ) => void;

    tapped(tapOn('n-2', { b: 2 }));
    tapped(tapOn('n-2', { b: 2 }));

    expect(opened).toHaveBeenCalledTimes(1);
  });

  it('opens nothing for a button on the notification — only the tap on its body', () => {
    const port = portWith({ projectId: null, iphonePush: false });
    const opened = jest.fn();
    port.onOpen(opened);
    const tapped = notifications.addNotificationResponseReceivedListener.mock.calls[0]![0] as (
      response: unknown,
    ) => void;

    tapped(tapOn('n-3', {}, 'some-action'));

    expect(opened).not.toHaveBeenCalled();
  });
});
