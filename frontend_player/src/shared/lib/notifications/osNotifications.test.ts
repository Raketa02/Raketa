/**
 * The one module that asks the OS, against the mocked native edge.
 *
 * Everything here is a translation rather than a rule, and every case is one
 * translation: what the SDK reports becomes one of three standings, a token that
 * cannot be read becomes *nothing to register*, and a platform that is neither
 * store becomes nothing at all.
 */

import { Platform } from 'react-native';

import { osMock, resetPhone, stubPhone } from '@/test-support/notifications';

import {
  OFFERS_CHANNEL,
  ask,
  ensureChannel,
  platform,
  pushToken,
  standing,
  timeSensitive,
} from './osNotifications';

/**
 * Which store this build came from, for one test.
 *
 * `Platform.OS` is a plain property on React Native's platform module and the
 * only way to say *this is an Android phone* from a test. It is restored after
 * every case, because a suite that left it set would be handing the next one a
 * phone it never asked for.
 */
function pretendPlatform(os: 'ios' | 'android' | 'web'): void {
  (Platform as unknown as { OS: string }).OS = os;
}

const REAL_PLATFORM = Platform.OS;

beforeEach(() => {
  resetPhone();
});

afterEach(() => {
  pretendPlatform(REAL_PLATFORM as 'ios' | 'android' | 'web');
});

describe('whether the OS prompt is still worth spending', () => {
  it('reads a granted install as granted', async () => {
    stubPhone({ granted: true, canAskAgain: false });

    await expect(standing()).resolves.toBe('granted');
  });

  it('reads a fresh install as askable', async () => {
    stubPhone({ granted: false, canAskAgain: true });

    await expect(standing()).resolves.toBe('askable');
  });

  it('reads a spent dialog as spent', async () => {
    stubPhone({ granted: false, canAskAgain: false });

    await expect(standing()).resolves.toBe('spent');
  });

  /**
   * **`canAskAgain` and not the raw status**, which is the whole of why this is
   * a translation rather than a pass-through. Android shows the dialog twice, so
   * a phone that has refused once has not been written off — reading a status of
   * *denied* alone would take that phone out of the pool a whole denial early.
   */
  it('reads a phone that refused once and may be asked again as askable', async () => {
    stubPhone({ granted: false, canAskAgain: true });

    await expect(standing()).resolves.toBe('askable');
  });

  it('fires nothing to find out', async () => {
    await standing();

    expect(osMock().requestPermissionsAsync).not.toHaveBeenCalled();
  });
});

describe('firing the prompt', () => {
  it('fires the system dialog and reports what it left behind', async () => {
    stubPhone({ answersPrompt: 'granted' });

    await expect(ask()).resolves.toBe('granted');
    expect(osMock().requestPermissionsAsync).toHaveBeenCalledTimes(1);
  });

  it('reports a refusal as a spent dialog', async () => {
    stubPhone({ answersPrompt: 'denied' });

    await expect(ask()).resolves.toBe('spent');
  });
});

describe('where this phone can be reached', () => {
  it('answers the Expo token', async () => {
    stubPhone({ token: 'ExponentPushToken[real]' });

    await expect(pushToken()).resolves.toBe('ExponentPushToken[real]');
  });

  /**
   * The state of every build until an Expo project id exists
   * (`Raketa02/Raketa#26`): the SDK throws outright. It is a missing credential
   * and not a failure a player could act on, so it becomes *nothing to register*
   * rather than an error that reaches a screen.
   */
  it('answers nothing rather than throwing when no token can be read', async () => {
    stubPhone({ token: undefined });

    await expect(pushToken()).resolves.toBeUndefined();
  });
});

describe('what Time Sensitive is set to', () => {
  /**
   * **`notSupported`, and it is the truth of this build rather than a stand-in.**
   * Apple reports it for an app holding no Time Sensitive entitlement and this
   * build holds none; Android has no such setting at all, which is the iPad case
   * `ADR-0065` names.
   *
   * What is *not* true is that it would still be right once the entitlement
   * ships: `expo-notifications` never reads
   * `UNNotificationSettings.timeSensitiveSetting`, on any platform, so there is
   * nothing to call. That is `Raketa02/Raketa#131`, and this case is what goes
   * red the day it is fixed.
   */
  it('is notSupported, on every phone, today', async () => {
    await expect(timeSensitive()).resolves.toBe('notSupported');
  });

  it('asks the OS nothing to say so', async () => {
    await timeSensitive();

    expect(osMock().getPermissionsAsync).not.toHaveBeenCalled();
  });
});

describe('the one Android channel', () => {
  it('is created at high importance, under the name the server addresses', async () => {
    pretendPlatform('android');
    await ensureChannel();

    expect(osMock().setNotificationChannelAsync).toHaveBeenCalledWith(
      OFFERS_CHANNEL,
      expect.objectContaining({ importance: 6 }),
    );
  });

  /**
   * The id the backend puts on every Android message. It is not on the contract,
   * so this is the only place the two spellings meet — `Raketa02/Raketa#130`.
   */
  it('is the id the server names', () => {
    expect(OFFERS_CHANNEL).toBe('offers');
  });

  /** Loudness on iOS is per message, so there is no channel to create. */
  it('is not created on iOS', async () => {
    pretendPlatform('ios');
    await ensureChannel();

    expect(osMock().setNotificationChannelAsync).not.toHaveBeenCalled();
  });

  /**
   * **One channel and not two** (`ADR-0065`). *Seats you asked for* and *seats
   * we found you* as separate channels is a mute switch on the rungs that never
   * asked, with no server-side signal that it was thrown.
   */
  it('is one channel however often it is ensured', async () => {
    pretendPlatform('android');
    await ensureChannel();
    await ensureChannel();

    const ids = osMock().setNotificationChannelAsync.mock.calls.map(([id]: [string]) => id);
    expect(new Set(ids)).toEqual(new Set([OFFERS_CHANNEL]));
  });

  /** Do Not Disturb bypass is a second permission, and `ADR-0065` declines it. */
  it('does not ask to bypass Do Not Disturb', async () => {
    pretendPlatform('android');
    await ensureChannel();

    const [, channel] = osMock().setNotificationChannelAsync.mock.calls[0] as [
      string,
      Record<string, unknown>,
    ];
    expect(channel.bypassDnd).toBeUndefined();
  });
});

describe('which store this build came from', () => {
  it.each(['ios', 'android'] as const)('answers %s', (os) => {
    pretendPlatform(os);

    expect(platform()).toBe(os);
  });

  /** Neither store means no registration at all — see `registerDevice`. */
  it('answers nothing anywhere else', () => {
    pretendPlatform('web');

    expect(platform()).toBeUndefined();
  });
});
