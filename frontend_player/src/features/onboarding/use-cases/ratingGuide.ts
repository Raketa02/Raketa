/**
 * **Whether this account has been shown the guide on _Your rating_ on this phone, and remembering
 * that it has** — the phone-preferences store's one flag kept past a session
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8, as amended
 * 2026-11-04): per account, as every value there is, and kept at sign-out. Pass-throughs, as
 * `lastSport` is: the store neither throws nor judges, and the rule is `ratingGuideIsDue`'s.
 */

import { raisePhoneFlag, readPhoneFlag } from '@/shared/lib/preferences';

export function readRatingGuideShown(account: string): Promise<boolean> {
  return readPhoneFlag(account, 'ratingGuideShown');
}

export function rememberRatingGuideShown(account: string): Promise<void> {
  return raisePhoneFlag(account, 'ratingGuideShown');
}
