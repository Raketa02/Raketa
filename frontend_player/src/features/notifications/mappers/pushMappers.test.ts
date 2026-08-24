import type { DeviceAddress } from '../domain/DeviceAddress';

import { toRegisterDeviceRequest } from './pushMappers';

const PHONE: DeviceAddress = {
  token: 'ExponentPushToken[abc]',
  platform: 'ios',
  timeSensitive: 'enabled',
};

describe('one phone, as the wire takes it', () => {
  it('sends the token, the platform and the setting, under the wire’s own names', () => {
    expect(toRegisterDeviceRequest(PHONE)).toEqual({
      token: 'ExponentPushToken[abc]',
      platform: 'ios',
      time_sensitive_setting: 'enabled',
    });
  });

  /**
   * **All three values cross, and each is carried rather than derived.**
   * `ADR-0065` makes `notSupported` a fourth value and not a synonym for a
   * refusal — a player on an iPad was never going to get a Focus-piercing alert
   * and has refused nothing — so a mapper that folded two of them together
   * would destroy the one distinction the field exists to carry.
   */
  it.each(['enabled', 'disabled', 'notSupported'] as const)('carries %s unchanged', (setting) => {
    expect(toRegisterDeviceRequest({ ...PHONE, timeSensitive: setting })).toMatchObject({
      time_sensitive_setting: setting,
    });
  });

  it('carries either platform unchanged', () => {
    expect(toRegisterDeviceRequest({ ...PHONE, platform: 'android' })).toMatchObject({
      platform: 'android',
    });
  });

  /**
   * The request body is exactly three fields. A fourth would be a fact about
   * this phone that the server never asked for and cannot store.
   */
  it('sends nothing else at all', () => {
    expect(Object.keys(toRegisterDeviceRequest(PHONE)).sort()).toEqual([
      'platform',
      'time_sensitive_setting',
      'token',
    ]);
  });
});
