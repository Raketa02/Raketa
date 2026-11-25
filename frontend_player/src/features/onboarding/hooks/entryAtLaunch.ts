/**
 * **Where the entry gate will send this launch, asked before any screen exists** (#874; ADR-0209 §2,
 * amended 2026-11-24) — so that Home's reads set out during the splash only for an account headed
 * for the tabs.
 *
 * It decides from what the gate decides from, and by the same rule (`entryDestinationOf`): **the
 * account session restore left in the cache**, and — for an account that runs a club's groups,
 * whose launch waits for it (`decidedByTheLastProfile`) — **the profile the phone says it wore
 * last**, read under the gate's own definition so the gate finds it settled. With no account cached
 * (the check failed, was refused, or was never sent on a phone known to be offline) there is nothing
 * to decide from, and nothing is: `undefined`, as it is when the phone cannot be read.
 */

import type { QueryClient } from '@tanstack/react-query';

import { currentUserQuery, fetchLastProfile } from '@/features/auth/types';

import { decidedByTheLastProfile, type EntryDestination } from '../domain/entryDecision';
import { entryDestinationOf } from '../use-cases/entryDestination';

export async function entryDestinationAtLaunch(
  client: QueryClient,
): Promise<EntryDestination | undefined> {
  const account = client.getQueryData(currentUserQuery().queryKey);
  if (account === undefined) return undefined;
  if (!decidedByTheLastProfile(account.profiles)) return entryDestinationOf(account);
  try {
    return entryDestinationOf(account, await fetchLastProfile(client, account.id));
  } catch {
    return undefined;
  }
}
