/**
 * **The phone-preferences store** — the choices a player made that the phone keeps for them, per
 * account, until they sign out
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)).
 * The second module in the app allowed to import AsyncStorage, beside the flag datafile cache.
 *
 * **A choice, never a copy of the server.** What is kept here is what a player picked on this
 * phone — which Play segment they were on — and nothing the backend knows. The table in §2 is the
 * limit: a new value is a new record, not a line added below.
 *
 * **Per account.** Every value is stored under the account that chose it, so a second person
 * signing in on the same phone starts from the defaults rather than from somebody else's habits.
 * **Forgotten at sign-out**: `endSession` calls `forgetPhonePreferences`, whichever way the
 * session ended — a tap on *Sign out*, or the server refusing the credentials — because the store
 * cannot tell *me again* from *somebody else*.
 *
 * **Why `shared/lib` and not a feature.** Three features will each own one value (the Play
 * segment now, the last sport and the last profile later), and the sign-out sequence in
 * `shared/lib/auth` has to empty it — `shared/` may never import a feature.
 *
 * **Why AsyncStorage.** Not the keychain: that is the credentials store, and one module owning it
 * is what keeps token lifetime auditable (ADR-0008). Not the server: Play would wait on a round
 * trip before it could choose a segment. And **never a credential here** — the lint fence that
 * admits this file says so, and `scripts/test-import-boundaries.sh` proves the fence still holds
 * beside it.
 *
 * **Nothing here throws, and nothing here judges a value.** A read that fails is *nothing saved*;
 * a write that fails loses only the next launch's copy. Whether a saved value still means
 * something — a segment this build has never heard of, a sport the player is no longer rated in —
 * is the owning feature's check on read (§4), because only it knows what the value is.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * **The values the phone may keep** (ADR-0188 §2). One today; the last sport (#513) and the last
 * profile (#518) join it, and a value not listed here cannot be stored.
 */
export type PhonePreference = 'playSegment';

/** Every key this module writes starts with this, and nothing else's does. */
const PREFIX = 'raketa.phone-preferences.';

/** One entry per account per value — a read never has to parse what it did not ask for. */
function keyFor(account: string, preference: PhonePreference): string {
  return `${PREFIX}${account}.${preference}`;
}

/** What this account saved, **unchecked** — the owning feature decides whether it still means anything. */
export async function readPhonePreference(
  account: string,
  preference: PhonePreference,
): Promise<string | undefined> {
  try {
    const saved = await AsyncStorage.getItem(keyFor(account, preference));
    return saved ?? undefined;
  } catch {
    return undefined;
  }
}

/** Keep this account's choice, replacing the one before. */
export async function savePhonePreference(
  account: string,
  preference: PhonePreference,
  value: string,
): Promise<void> {
  try {
    await AsyncStorage.setItem(keyFor(account, preference), value);
  } catch {
    // The choice stands for this session; only the next launch's copy is lost.
  }
}

/**
 * **Forget every account's choices** — a step of the sign-out sequence (ADR-0188 §3). The flag
 * datafile the other AsyncStorage module keeps is left alone: it names nobody.
 */
export async function forgetPhonePreferences(): Promise<void> {
  try {
    const keys = await AsyncStorage.getAllKeys();
    const ours = keys.filter((key) => key.startsWith(PREFIX));
    if (ours.length > 0) await AsyncStorage.multiRemove(ours);
  } catch {
    // A store that cannot be listed cannot be emptied either; the next sign-in's account key is
    // what keeps a leftover value from being read by anybody but its owner.
  }
}
