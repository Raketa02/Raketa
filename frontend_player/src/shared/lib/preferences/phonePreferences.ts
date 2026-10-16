/**
 * **The phone-preferences store** — the choices a player made that the phone keeps for them, per
 * account, until they sign out
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)).
 * The second module in the app allowed to import AsyncStorage, beside the flag datafile cache.
 *
 * **A choice, never a copy of the server.** What is kept here is what a player picked on this
 * phone — which Play segment they were on, which sport they last filtered a group by — and
 * nothing the backend knows. The table in §2 is the
 * limit: a new value is a new record, not a line added below.
 *
 * **Per account.** Every value is stored under the account that chose it, so a second person
 * signing in on the same phone starts from the defaults rather than from somebody else's habits.
 * **Forgotten at sign-out**: `endSession` calls `forgetPhonePreferences`, whichever way the
 * session ended — a tap on *Sign out*, or the server refusing the credentials — because the store
 * cannot tell *me again* from *somebody else*.
 *
 * **Why `shared/lib` and not a feature.** Four features each own one value (the shell the Play
 * segment, groups the last sport, auth the last profile, and proposals the opened games), and the
 * sign-out sequence in `shared/lib/auth` has to empty it — `shared/` may never import a feature.
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
 * **The values the phone may keep** (ADR-0188 §2): the Play segment (#512), the sport last picked
 * in a group's fast filter (#513) and the profile an account with two wore last (#518). The table
 * is full: a value not listed here cannot be stored, and a fourth is a new record.
 *
 * **A fourth since [#556](https://github.com/Raketa02/Raketa/issues/556)**: the booked games whose
 * details this account has opened, which is what keeps a game on Home *new until opened* (the
 * mechanics §11.4). It is what the player did on this phone rather than a copy of anything the
 * server knows — no read says whether a game was opened — and it obeys the table's two rules, per
 * account and forgotten at sign-out. **That record is owed, from a root session** — or the product
 * owner's ruling that *new* lives elsewhere — and until it exists this value stands outside the
 * table ADR-0188 §2 accepted.
 */
export type PhonePreference =
  'playSegment' | 'lastSport' | 'lastProfile' | 'openedGames' | 'dismissedGames';

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
