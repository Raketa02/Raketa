/**
 * Tell the platform where this phone is, and what it can be sent.
 *
 * Four steps and three ways to stop early, and every stop is silent: a player
 * has nothing to do about any of them, and nothing on any screen depends on the
 * outcome. `ADR-0061` is explicit that refusing notifications costs her the
 * message and never the card — and a build that cannot produce a token is the
 * same loss arriving for a different reason.
 *
 * **The channel is created before the server is told where to send**, so there
 * is no window in which a message could be addressed to a phone that has nowhere
 * to display it. On iOS that step is a no-op; on Android a message naming a
 * channel that was never created is `ADR-0065`'s one high-importance channel
 * silently downgraded to the default one.
 *
 * **The reported setting is read at the moment of registering**, never
 * remembered. That is the whole point of `ADR-0065`'s observability argument:
 * revocation happens *after* a grant, so a value captured once at the moment she
 * said yes would report that every player still has Time Sensitive on for ever.
 * The corollary is that this has to run more than once — see `hooks/`.
 */

import type { DeviceKind, TimeSensitiveReading } from '@/shared/lib/notifications';

import { registerDevice as putDevice } from '../api/pushApi';
import type { DeviceAddress } from '../domain/DeviceAddress';
import { toRegisterDeviceRequest } from '../mappers/pushMappers';

/**
 * What this use-case needs from the OS.
 *
 * Declared here and injected rather than imported, so the workflow stays pure
 * TypeScript and every one of its branches is drivable without a device. The
 * shape is checked against the real adapter in one place — `hooks/`.
 */
export interface DeviceReader {
  /** Which store this build came from, or neither. */
  readonly platform: () => DeviceKind | undefined;
  /** Where to reach this phone, or `undefined` when it cannot be reached. */
  readonly pushToken: () => Promise<string | undefined>;
  readonly timeSensitive: () => Promise<TimeSensitiveReading>;
  /** Create the one Android channel. A no-op on iOS. */
  readonly ensureChannel: () => Promise<void>;
}

export interface RegisterDeviceOptions {
  readonly signal?: AbortSignal;
}

/**
 * The address that was registered, or `undefined` when there was none to send.
 *
 * The answer is returned rather than discarded because it is the one thing a
 * test can assert *and* the one thing a future caller might want — but nothing
 * reads it today, and nothing may branch on the setting inside it.
 */
export async function registerDevice(
  os: DeviceReader,
  { signal }: RegisterDeviceOptions = {},
): Promise<DeviceAddress | undefined> {
  const platform = os.platform();
  if (platform === undefined) return undefined;

  const token = await os.pushToken();
  if (token === undefined) return undefined;

  const address: DeviceAddress = {
    token,
    platform,
    timeSensitive: await os.timeSensitive(),
  };

  await os.ensureChannel();
  await putDevice({ body: toRegisterDeviceRequest(address), signal });
  return address;
}
