/**
 * **The profile an account wore last, on this phone** — read back and kept through the
 * phone-preferences store (ADR-0188 §2). Neither ever throws: the store swallows its own failures,
 * and an unreadable value is nothing chosen.
 */

import { readPhonePreference, savePhonePreference } from '@/shared/lib/preferences';

import { profileChoiceFrom, savedProfile, type ProfileChoice } from '../domain/lastProfile';

export async function readLastProfile(account: string): Promise<ProfileChoice | undefined> {
  return profileChoiceFrom(await readPhonePreference(account, 'lastProfile'));
}

export function keepLastProfile(account: string, choice: ProfileChoice): Promise<void> {
  return savePhonePreference(account, 'lastProfile', savedProfile(choice));
}
