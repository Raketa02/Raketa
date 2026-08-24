/**
 * Spend the OS prompt, and register the phone if it was granted.
 *
 * **This is the only path in the app that fires the system dialog** (`ADR-0061`:
 * *"the OS prompt is spent only on a yes"*), which is why *Not now* does not
 * call it rather than calling it with an argument: a code path that could fire
 * the prompt on the declining branch is one edit away from firing it.
 *
 * A grant registers the phone in the same breath, because the two are one act
 * from her side. A refusal does nothing at all — no request, no record, nothing
 * kept about the answer. There is no *she said no* fact anywhere in this client:
 * the OS holds it, and it is the only thing entitled to.
 */

import type { NotificationStanding } from '@/shared/lib/notifications';

import { registerDevice, type DeviceReader } from './registerDevice';

/** What this use-case needs from the OS, on top of `DeviceReader`'s four. */
export interface PermissionAsker extends DeviceReader {
  /** Fires the system dialog and answers what it left behind. */
  readonly ask: () => Promise<NotificationStanding>;
}

export interface AskForNotificationsOptions {
  readonly signal?: AbortSignal;
}

/**
 * What the OS says once the dialog has closed.
 *
 * The answer is returned so that a caller *could* act on it, and no caller does:
 * the explainer moves on identically either way, which is the same rule the
 * screen states out loud — refusing costs her the message and never a card.
 */
export async function askForNotifications(
  os: PermissionAsker,
  { signal }: AskForNotificationsOptions = {},
): Promise<NotificationStanding> {
  const standing = await os.ask();
  if (standing === 'granted') await registerDevice(os, { signal });
  return standing;
}
