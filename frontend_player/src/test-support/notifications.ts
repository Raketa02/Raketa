/**
 * The phone's notification settings, as a test harness.
 *
 * `expo-notifications` is mocked once in `jest.setup.js` — the same native edge
 * the keychain and the connectivity module are — and this is how a suite says
 * what that phone is currently answering. A second `jest.mock` in a suite would
 * be a second answer to *what does a phone look like here*.
 *
 * The default that setup installs is a **fresh install**: nothing granted, the
 * one system prompt unspent. Everything below moves it off that default.
 *
 * Not app code — nothing under `src/` imports this, so Metro never bundles it.
 */

export const PUSH_DEVICE_PATH = '/api/v1/push/device';

interface NotificationsModule {
  readonly getPermissionsAsync: jest.Mock;
  readonly requestPermissionsAsync: jest.Mock;
  readonly getExpoPushTokenAsync: jest.Mock;
  readonly setNotificationChannelAsync: jest.Mock;
}

/** The mocked module, for a suite that wants to count calls to the OS. */
export function osMock(): NotificationsModule {
  return jest.requireMock('expo-notifications') as NotificationsModule;
}

export interface PhoneSettings {
  /** What `getPermissionsAsync` reports before anything is asked. */
  readonly granted?: boolean;
  /** Whether the system dialog would still be shown. */
  readonly canAskAgain?: boolean;
  /** What the dialog leaves behind when it is fired. */
  readonly answersPrompt?: 'granted' | 'denied';
  /**
   * The Expo token, or `undefined` for a build that cannot read one — which is
   * every build until an Expo project id exists (`Raketa02/Raketa#26`).
   */
  readonly token?: string | undefined;
}

/**
 * Put the phone in a state. Call in a test, after `resetPhone`.
 *
 * `answersPrompt` is what the dialog does **when it is fired**, which is a
 * different fact from what `getPermissionsAsync` reports before it — and keeping
 * them apart is what lets a suite prove that *Not now* never fired it: the
 * standing stays exactly where it started.
 */
export function stubPhone(settings: PhoneSettings = {}): void {
  const { granted = false, canAskAgain = true, answersPrompt = 'granted' } = settings;
  // `in` rather than a destructuring default, because *no token* is one of the
  // states this harness exists to describe — and a default would quietly turn
  // `{ token: undefined }` back into a phone that has one.
  const token = 'token' in settings ? settings.token : 'ExponentPushToken[test]';
  const os = osMock();

  os.getPermissionsAsync.mockImplementation(async () => ({ granted, canAskAgain }));
  os.requestPermissionsAsync.mockImplementation(async () =>
    answersPrompt === 'granted'
      ? { granted: true, canAskAgain: false }
      : { granted: false, canAskAgain: false },
  );
  os.getExpoPushTokenAsync.mockImplementation(async () => {
    if (token === undefined) throw new Error('ERR_NOTIFICATIONS_NO_EXPERIENCE_ID');
    return { type: 'expo', data: token };
  });
  os.setNotificationChannelAsync.mockImplementation(async () => undefined);
}

/** Back to a fresh install, with every call count cleared. */
export function resetPhone(): void {
  const os = osMock();
  os.getPermissionsAsync.mockReset();
  os.requestPermissionsAsync.mockReset();
  os.getExpoPushTokenAsync.mockReset();
  os.setNotificationChannelAsync.mockReset();
  stubPhone();
}
