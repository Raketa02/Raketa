/**
 * **The rows seen on a group page's tab, kept on the phone** (ADR-0208, #849) — pass-throughs to the
 * phone-preferences store: one list of ids per account, group, sport and tab. What a stored value
 * means — and that a stale one means *nothing seen* — is the domain's (`seenFrom`).
 */

import {
  readPhonePreference,
  savePhonePreference,
  type SeenRowsPreference,
} from '@/shared/lib/preferences';
import type { Sport } from '@/shared/vocabulary/sport';

import { seenEntry, seenFrom, type SeenTab } from '../domain/seen';

/** The store's key for one tab's seen ids — the entry the domain spells, under the store's value. */
export function seenRowsPreference(
  groupId: string,
  sport: Sport,
  tab: SeenTab,
): SeenRowsPreference {
  return `seenRows.${seenEntry(groupId, sport, tab)}`;
}

/** The ids this account has seen on the tab — none for a value the phone cannot read. */
export async function readSeenRows(
  account: string,
  preference: SeenRowsPreference,
): Promise<readonly string[]> {
  return seenFrom(await readPhonePreference(account, preference));
}

export function keepSeenRows(
  account: string,
  preference: SeenRowsPreference,
  seen: readonly string[],
): Promise<void> {
  return savePhonePreference(account, preference, JSON.stringify(seen));
}
