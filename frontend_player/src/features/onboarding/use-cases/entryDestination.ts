/**
 * **Where a signed-in account belongs on launch, from the account itself** (#874) — the entry gate's
 * rule (`entryDestination`) read off the account as `/users/me` serves it, with the profile the phone
 * says it wore last.
 *
 * **Callable outside the gate's hook, so the gate and the launch always agree.** The gate asks it
 * once its reads have answered (`useEntryDecision`); the launch asks it before any screen exists, so
 * that Home's reads set out during the splash only for an account the gate will send to the tabs —
 * never for one headed for the naming, the profile steps, a club's area or *Start playing*
 * (ADR-0209 §2, amended 2026-11-24). One reading of the account into the rule, here, is what keeps
 * the two from drifting apart: a copy in each caller is two answers to one question.
 */

import { named, type AuthenticatedUser, type ProfileChoice } from '@/features/auth/types';

import { entryDestination, type EntryDestination } from '../domain/entryDecision';

/**
 * @param lastProfile what the phone holds for this account — absent for nothing chosen. It decides
 * only for an account that runs a club's groups (`decidedByTheLastProfile`), and a caller must have
 * read it before asking for one.
 */
export function entryDestinationOf(
  account: Pick<AuthenticatedUser, 'nickname' | 'hasPlayerProfile' | 'profiles'>,
  lastProfile?: ProfileChoice,
): EntryDestination {
  return entryDestination({
    // A nickname (ADR-0199 §3): an account an Invitation opened holds none either, and the naming is
    // still owed once it plays.
    named: named(account),
    hasPlayerProfile: account.hasPlayerProfile,
    profiles: account.profiles,
    ...(lastProfile === undefined ? {} : { lastProfile }),
  });
}
