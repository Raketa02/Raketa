/**
 * **The keys a phone preference is held under in the Query cache** — one per account per value,
 * beside the store's own one-per-account-per-value layout, and spelled once here so the three
 * features that each own one value (the Play segment, the last sport and the last profile) cannot
 * spell the root three ways.
 *
 * A preference is not server data, and Query holds it anyway: the read is asynchronous, the answer is
 * wanted at once on every later mount, and a sign-out's `queryClient.clear()` drops it with
 * everything else the session held. The account is in the key so that a second person signing in
 * never finds the first one's answer in memory either.
 */

import type { PhonePreference } from './phonePreferences';

export const phonePreferenceKeys = {
  all: ['phone-preferences'] as const,
  one: (account: string, preference: PhonePreference) =>
    [...phonePreferenceKeys.all, account, preference] as const,
};
