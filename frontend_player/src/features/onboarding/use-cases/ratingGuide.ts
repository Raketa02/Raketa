/**
 * **Whether this phone has shown the guide on _Your rating_, and remembering that it has** — the
 * phone-preferences store's one per-phone flag
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8): kept per
 * phone rather than per account, and kept at sign-out. Pass-throughs, as `lastSport` is: the
 * store neither throws nor judges, and the rule is `ratingGuideIsDue`'s.
 */

import { raisePhoneFlag, readPhoneFlag } from '@/shared/lib/preferences';

export function readRatingGuideShown(): Promise<boolean> {
  return readPhoneFlag('ratingGuideShown');
}

export function rememberRatingGuideShown(): Promise<void> {
  return raisePhoneFlag('ratingGuideShown');
}
