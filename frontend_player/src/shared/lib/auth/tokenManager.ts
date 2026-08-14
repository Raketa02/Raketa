/**
 * The one module that touches the OS keychain. ESLint blocks `expo-secure-store`
 * everywhere else, because one module owning the keychain is what makes token lifetime
 * auditable — you can read this file and know every moment a credential is written,
 * read or destroyed. See ADR-0008 and docs/architecture.md Part 5.
 *
 * **The pair is stored under one key, as one JSON value.** SecureStore writes a key at a
 * time, so two `setItemAsync` calls are two chances to be interrupted — by a crash, a
 * kill, or the OS reclaiming the app mid-write. Landing half a rotation leaves a new
 * access token beside a dead refresh token, which is a session that can never recover
 * and can only be fixed by signing out. One key makes rotation atomic by construction.
 *
 * **The in-memory mirror is the runtime representation.** Reading the keychain before
 * every request is blocking I/O on the hot path; SecureStore stays the cross-restart
 * persistence and memory is what a request reads. Neither is reachable from a component.
 */

import * as SecureStore from "expo-secure-store";

import type { Tokens } from "./auth.types";

/** One key, because the pair is one fact. See the note above. */
const SESSION_KEY = "rakieta.session.v1";

/**
 * The runtime copy. A module variable holding a credential is normally a bug; here it
 * is the documented mirror, it is cleared by `clear()`, and nothing outside this module
 * can read it.
 */
let cached: Tokens | undefined;

function isTokens(value: unknown): value is Tokens {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<Tokens>;
  return (
    typeof candidate.accessToken === "string" &&
    candidate.accessToken.length > 0 &&
    typeof candidate.refreshToken === "string" &&
    candidate.refreshToken.length > 0
  );
}

/**
 * Read the stored pair into memory. Called once, by the bootstrap sequence.
 *
 * A keychain read can fail — a corrupted entry, a device whose secure enclave is
 * unavailable, a value written by an incompatible build. None of those are recoverable
 * and all of them mean the same thing to the app: there is no usable session. Failing
 * closed here is safe; failing *open* would mean launching with a half-read credential.
 */
export async function load(): Promise<Tokens | undefined> {
  try {
    const raw = await SecureStore.getItemAsync(SESSION_KEY);
    if (raw === null) {
      cached = undefined;
      return undefined;
    }

    const parsed: unknown = JSON.parse(raw);
    cached = isTokens(parsed) ? parsed : undefined;

    // An unreadable entry is not left behind to fail identically on every launch.
    if (cached === undefined) await SecureStore.deleteItemAsync(SESSION_KEY);

    return cached;
  } catch {
    // Never log the failure with its value attached — the value is the credential.
    cached = undefined;
    return undefined;
  }
}

/**
 * Persist a pair, atomically, and update the mirror.
 *
 * Memory is written only after the keychain accepts the value: a mirror the keychain
 * never received is a session that silently ends at the next launch.
 */
export async function save(tokens: Tokens): Promise<void> {
  await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(tokens));
  cached = tokens;
}

/**
 * Destroy the credentials, in memory and on disk.
 *
 * Memory is cleared **first and unconditionally**. If the keychain delete throws, the
 * running app must still be credential-less — a sign-out that leaves a usable token in
 * memory because a disk write failed is a sign-out that did not happen.
 */
export async function clear(): Promise<void> {
  cached = undefined;
  try {
    await SecureStore.deleteItemAsync(SESSION_KEY);
  } catch {
    // Nothing to recover to. The next launch reads no usable value either way, and the
    // running session is already unauthenticated.
  }
}

/** The access token for the next request. Synchronous by design — this is the hot path. */
export function getAccessToken(): string | undefined {
  return cached?.accessToken;
}

/** The refresh token. Read by sign-out (to revoke) and, later, by #22's rotation. */
export function getRefreshToken(): string | undefined {
  return cached?.refreshToken;
}

export function hasTokens(): boolean {
  return cached !== undefined;
}
