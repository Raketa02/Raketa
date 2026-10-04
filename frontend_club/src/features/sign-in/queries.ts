import 'server-only';

import { readRecovery } from '@/server/recovery';
import { readSession } from '@/server/session';

/**
 * **What the signed-out pages ask of the server before they draw.** Whether a session cookie
 * is present is enough for the root to choose between sign-in and Overview; whether it still
 * works is the backend's to say, on the first signed-in read.
 */
export async function hasSession(): Promise<boolean> {
  return (await readSession()) !== null;
}

/** The email the recovery under way was asked with, offered back on its pages. */
export async function recoveryEmail(): Promise<string> {
  return (await readRecovery())?.email ?? '';
}

/** Whether a right code has been claimed, so *Set a new password* has a ticket to spend. */
export async function hasTicket(): Promise<boolean> {
  return (await readRecovery())?.ticket !== undefined;
}
