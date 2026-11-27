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
 * **Why `shared/lib` and not a feature.** Five features each own their values (the shell the Play
 * segment, groups the last sport, auth the last profile, proposals the opened games and the rows
 * seen on a group page's tabs, and rankings the view), and the sign-out sequence in
 * `shared/lib/auth` has to empty it — `shared/` may never
 * import a feature.
 *
 * **Why AsyncStorage.** Not the keychain: that is the credentials store, and one module owning it
 * is what keeps token lifetime auditable (ADR-0008). Not the server: Play would wait on a round
 * trip before it could choose a segment. And **never a credential here** — the lint fence that
 * admits this file says so, and `scripts/test-import-boundaries.sh` proves the fence still holds
 * beside it.
 *
 * **And one flag kept past a session** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §8): *the guide on Your rating was shown*, per account like every value here, but kept at
 * sign-out — see {@link PhoneFlag}. The second rule above holds for every value but that one.
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
 *
 * **And the Rankings view** ([#777](https://github.com/Raketa02/Raketa/issues/777)), *General* or
 * *Friends* — the view last looked at on the Rankings page, which Home's trophy reads too. It is the
 * per-account value [ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md)
 * adds to ADR-0188's table, so its record exists; per account and forgotten at sign-out like the rest.
 *
 * **And the rows seen on a group page's tabs** ([#849](https://github.com/Raketa02/Raketa/issues/849)),
 * the value [ADR-0208](../../../../../docs/adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md)
 * adds — see {@link SeenRowsPreference}.
 */
export type PhonePreference =
  | 'playSegment'
  | 'lastSport'
  | 'lastProfile'
  | 'openedGames'
  | 'dismissedGames'
  | 'rankingView'
  | SeenRowsPreference;

/**
 * **The rows a player has seen on a group page's tab** (ADR-0208) — the ids on Games, Fill in and
 * You’re in that were on screen, which is what a tab's badge is counted against: one JSON list of
 * ids **per group, sport and tab**, and on Games per kind (#850), each under its own key,
 * `seenRows.` and then the entry `proposals` spells. Per account and forgotten at sign-out, like the rest of the table; only
 * ids, cut back to the ones the tab still counts every time it is written (§2), so it never grows
 * past the tab; and **read and written without waiting** (§5) — the one value here whose read no
 * screen holds its first frame for.
 */
export type SeenRowsPreference = `seenRows.${string}`;

/** Every key this module writes starts with this, and nothing else's does. */
const PREFIX = 'rakieta.phone-preferences.';

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
 * **The flags the phone keeps for an account** — per account like every value, but **kept at
 * sign-out** ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8,
 * amending ADR-0188 §2). One today: the guide on *Your rating* was shown to this account, finished
 * or skipped. The ruling was *once per phone* until 2026-11-04 and is *once per account on a
 * phone* since: the same account signing in again never sees it, and a second account on the
 * phone sees it once of its own.
 *
 * A flag rather than a value: it is down until something raises it, and nothing lowers one. It
 * outlives a session, so it lives under a prefix of its own, which `forgetPhonePreferences` never
 * lists. The once-per-phone flag's key had no account in it; nothing reads it any more, so every
 * account on a phone that raised it is shown the guide once more.
 */
export type PhoneFlag = 'ratingGuideShown';

const FLAG_PREFIX = 'rakieta.phone-flags.';

/** One entry per account per flag, as a value's is. */
function flagKeyFor(account: string, flag: PhoneFlag): string {
  return `${FLAG_PREFIX}${account}.${flag}`;
}

/** The value a raised flag is stored as — any other stored string reads as down. */
const RAISED = 'raised';

/** Whether this account ever raised the flag on this phone. A read that fails is *never*, as a value's is *nothing saved*. */
export async function readPhoneFlag(account: string, flag: PhoneFlag): Promise<boolean> {
  try {
    return (await AsyncStorage.getItem(flagKeyFor(account, flag))) === RAISED;
  } catch {
    return false;
  }
}

/** Raise the account's flag on this phone for good. */
export async function raisePhoneFlag(account: string, flag: PhoneFlag): Promise<void> {
  try {
    await AsyncStorage.setItem(flagKeyFor(account, flag), RAISED);
  } catch {
    // The flag stands for this session in whoever holds it; only the next launch's copy is lost.
  }
}

/**
 * **The flags the phone keeps for itself** — under no account, and kept at sign-out
 * ([#756](https://github.com/Raketa02/Raketa/issues/756)). One: *the install referrer was read*,
 * which an Android phone does on the app's first launch, before anybody has signed in (the friends
 * mechanics §4.3). It is a fact about this installation, not about whoever uses it: the link Google
 * Play carried through the install is opened once, and never handed to a later account.
 *
 * **It stands outside ADR-0188 §2's table, which lists per-account values** — as `openedGames` does,
 * the record is owed from a root session, or the product owner's ruling that *once* lives elsewhere.
 *
 * **A read that fails reads as raised**, unlike an account's flag: the one flag here guards a link
 * being acted on, and acting on a stale one on every launch is the worse of the two mistakes — the
 * person who loses the referrer still has the site's *Open in Rakieta*.
 */
export type PhoneWideFlag = 'installReferrerRead';

const PHONE_WIDE_PREFIX = 'rakieta.phone-wide-flags.';

/** One entry per flag, under no account. */
function phoneWideKeyFor(flag: PhoneWideFlag): string {
  return `${PHONE_WIDE_PREFIX}${flag}`;
}

/** Whether this phone ever raised the flag — `true` when the store cannot be read, as above. */
export async function readPhoneWideFlag(flag: PhoneWideFlag): Promise<boolean> {
  try {
    return (await AsyncStorage.getItem(phoneWideKeyFor(flag))) === RAISED;
  } catch {
    return true;
  }
}

/** Raise the phone's flag for good. */
export async function raisePhoneWideFlag(flag: PhoneWideFlag): Promise<void> {
  try {
    await AsyncStorage.setItem(phoneWideKeyFor(flag), RAISED);
  } catch {
    // Only the next launch's copy is lost — and it reads the store the way this one could not.
  }
}

/**
 * **Forget every account's choices** — a step of the sign-out sequence (ADR-0188 §3). The flag
 * datafile the other AsyncStorage module kept named nobody and was left alone, and so are the
 * flags kept past a session (ADR-0200 §8, and the phone's own, #756): they are under prefixes this
 * never lists.
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
