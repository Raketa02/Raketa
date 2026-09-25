/**
 * **Reading and keeping the last sport** — the sport last picked in any group's fast filter, the
 * phone-preferences store's second value
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §2), per account.
 *
 * The store hands back a string it has not judged, and so does this: whether it is still a sport
 * the player is rated in needs the ratings, and `openingSport` is the judgement (§4). Neither
 * function throws — the store never does — so a phone whose storage cannot be read opens on the
 * default.
 */

import { readPhonePreference, savePhonePreference } from '@/shared/lib/preferences';
import type { Sport } from '@/shared/vocabulary/sport';

/** What this account last picked, **unchecked** — `null` for nothing, since a query may not answer `undefined`. */
export async function readLastSport(account: string): Promise<string | null> {
  return (await readPhonePreference(account, 'lastSport')) ?? null;
}

export function keepLastSport(account: string, sport: Sport): Promise<void> {
  return savePhonePreference(account, 'lastSport', sport);
}
