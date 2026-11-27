/**
 * **The last good datafile, kept on the device** — and one of the two modules in the app allowed
 * to import AsyncStorage, beside the phone-preferences store (ADR-0188).
 *
 * ADR-0206 §6's middle rung: each datafile the app could read is saved here, raw, and read back
 * on the next launch, so a player who lost signal keeps the feature flags they last saw rather
 * than the code defaults. There is no bundled snapshot below it — a committed copy drifts
 * silently — so after this comes only the code default.
 *
 * **Why AsyncStorage, and why here.** The lint bans it everywhere else under `src/`, because
 * it is plaintext and the thing it must never hold is a credential
 * ([ADR-0008](../../../../../docs/adr/0008-player-mobile-securestore-direct-api.md)). A datafile
 * is not one: it is public-read by design and names no player (§9). SecureStore is the wrong
 * tool for the opposite reason — it is for small secrets, and this is neither. The exemption is
 * this one file wide, and `scripts/test-import-boundaries.sh` proves the ban still holds beside it
 * and beside the store, its other owner.
 *
 * **Nothing here throws.** A read that fails, or finds something that does not parse, is *no
 * cache*; a write that fails leaves the datafile in use in memory and loses only the next launch's
 * copy. Neither is worth a player noticing, and neither can make the app worse than its code
 * defaults.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

import type { AppEnvironment } from '@/shared/config/env';

import type { Datafile } from '../domain/featureFlags';

/**
 * One entry per environment. A device runs one environment, so this is one entry in practice —
 * and keying it anyway means a build pointed at a different environment can never read another's
 * feature flags as its own.
 */
function keyFor(environment: AppEnvironment): string {
  return `raketa.feature-flags.datafile.${environment}`;
}

/** What was saved last, parsed but **unchecked** — `schemas/` decides whether it is a datafile. */
export async function readSavedDatafile(environment: AppEnvironment): Promise<unknown> {
  try {
    const saved = await AsyncStorage.getItem(keyFor(environment));
    return saved === null ? undefined : (JSON.parse(saved) as unknown);
  } catch {
    return undefined;
  }
}

/** Keep a datafile the app has checked it can read, replacing the one before. */
export async function saveDatafile(environment: AppEnvironment, datafile: Datafile): Promise<void> {
  try {
    await AsyncStorage.setItem(keyFor(environment), JSON.stringify(datafile));
  } catch {
    // The datafile is already in use for this session; only the next launch's copy is lost.
  }
}
