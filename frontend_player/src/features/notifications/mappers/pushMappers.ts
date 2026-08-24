/**
 * One phone, as the wire takes it. The whole of this feature's wire boundary.
 *
 * Three fields, all required, and the requirement is the backend's own decision:
 * a client that could omit `time_sensitive_setting` would be reporting *disabled*
 * by silence, and `notSupported` is a fourth value rather than a synonym for a
 * refusal (`ADR-0065`).
 *
 * **It maps and asserts nothing.** There is no rule to hold — no default, no
 * fallback, no branch — because the two vocabularies are pinned equal to the
 * OS's in `codes.ts` and a value that could not cross has already failed
 * `pnpm typecheck` there.
 */

import type { DeviceAddress } from '../domain/DeviceAddress';

import type { RegisterDeviceRequest } from './codes';

/** The body of `PUT /api/v1/push/device`. */
export function toRegisterDeviceRequest(address: DeviceAddress): RegisterDeviceRequest {
  return {
    token: address.token,
    platform: address.platform,
    time_sensitive_setting: address.timeSensitive,
  };
}
