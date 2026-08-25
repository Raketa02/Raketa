/**
 * The location port, over a faked `expo-location`.
 *
 * The native module is the only thing stubbed. What is under test is the part this app
 * owns: which of the four states a native response becomes, what a fix looks like once it
 * has left Expo's shape, and — the assertion this file exists for — that the port never
 * reaches for a background permission.
 */

import { deviceLocation } from './location';

const native = jest.requireMock('expo-location') as {
  getForegroundPermissionsAsync: jest.Mock;
  requestForegroundPermissionsAsync: jest.Mock;
  getCurrentPositionAsync: jest.Mock;
  getBackgroundPermissionsAsync: jest.Mock;
  requestBackgroundPermissionsAsync: jest.Mock;
  startLocationUpdatesAsync: jest.Mock;
  watchPositionAsync: jest.Mock;
};

const granted = { granted: true, canAskAgain: false, status: 'granted' };
const blocked = { granted: false, canAskAgain: false, status: 'denied' };

// The defaults are restated rather than inherited from jest.setup.js. `clearAllMocks`
// forgets calls but keeps implementations, so a `mockResolvedValue` set by one case would
// otherwise still be in force in the next one — which is the kind of order-dependence that
// passes locally and fails on a machine that shards differently.
beforeEach(() => {
  jest.clearAllMocks();
  native.getForegroundPermissionsAsync.mockResolvedValue({
    granted: false,
    canAskAgain: true,
    status: 'undetermined',
  });
  native.requestForegroundPermissionsAsync.mockResolvedValue(granted);
  native.getCurrentPositionAsync.mockResolvedValue({
    coords: { latitude: 41.3874, longitude: 2.1686, accuracy: 12 },
    timestamp: 0,
  });
});

describe('the location permission', () => {
  it('reports the state without prompting anybody', async () => {
    await expect(deviceLocation.getPermission()).resolves.toBe('undetermined');
    expect(native.requestForegroundPermissionsAsync).not.toHaveBeenCalled();
  });

  it('reports what the player answered when it does ask', async () => {
    await expect(deviceLocation.requestPermission()).resolves.toBe('granted');
  });

  it('reports a permanent refusal as blocked, so a screen can send the player to Settings', async () => {
    native.getForegroundPermissionsAsync.mockResolvedValue(blocked);
    await expect(deviceLocation.getPermission()).resolves.toBe('blocked');
  });
});

describe('reading one fix', () => {
  it('produces the coordinates and the accuracy the device itself reports', async () => {
    await expect(deviceLocation.readFix()).resolves.toEqual({
      latitude: 41.3874,
      longitude: 2.1686,
      accuracyMetres: 12,
    });
  });

  /**
   * Not every platform reports an accuracy. `null` is carried through rather than
   * substituted with a number, because an invented radius is a claim about how well the
   * device knows where it is.
   */
  it('carries a missing accuracy through as null', async () => {
    native.getCurrentPositionAsync.mockResolvedValue({
      coords: { latitude: 1, longitude: 2, accuracy: null },
      timestamp: 0,
    });
    await expect(deviceLocation.readFix()).resolves.toEqual({
      latitude: 1,
      longitude: 2,
      accuracyMetres: null,
    });
  });

  /**
   * A refused permission, location services switched off, and a device that simply cannot
   * see the sky all arrive here as a rejection. All three mean the same thing to the
   * player — there is no area, and what that costs has to be said — so the port answers
   * "no fix" rather than making every caller write a try/catch around a native error class.
   */
  it('answers with no fix rather than throwing when the device cannot produce one', async () => {
    native.getCurrentPositionAsync.mockRejectedValue(new Error('Location request failed'));
    await expect(deviceLocation.readFix()).resolves.toBeNull();
  });
});

/**
 * A background location permission turns a location into a movement trail, which is a
 * different privacy class from the one this app asked the player about. There is no
 * product decision behind it, so there is no code that could take one by accident.
 */
describe('foreground only', () => {
  it('never asks for, checks, or starts a background location', async () => {
    await deviceLocation.getPermission();
    await deviceLocation.requestPermission();
    await deviceLocation.readFix();

    expect(native.getBackgroundPermissionsAsync).not.toHaveBeenCalled();
    expect(native.requestBackgroundPermissionsAsync).not.toHaveBeenCalled();
    expect(native.startLocationUpdatesAsync).not.toHaveBeenCalled();
    expect(native.watchPositionAsync).not.toHaveBeenCalled();
  });
});
