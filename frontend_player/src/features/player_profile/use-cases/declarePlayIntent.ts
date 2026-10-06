/**
 * Record what kind of game this player wants, in one sport.
 *
 * **The search screen is the edit surface, not a settings screen** (ADR-0094): a searcher with
 * a rating and no declaration is gated by a one-tap interstitial, *"permanent, not a migration
 * path"* — it is what makes the coverage rule true rather than merely intended, and it closes
 * a sport rated before the declaration shipped, a restored account and a bug in the tail with
 * one screen.
 *
 * `surface` is context recorded beside the fact and never something a decision reads, so it is
 * named at the call site rather than defaulted here — the two screens that will call this
 * declare from different places and only they know which.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { PlayIntent } from '@/shared/vocabulary/playIntent';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  declarePlayIntent as putPlayIntent,
  type PlayIntentSurface,
} from '../api/playerProfileApi';
import { toPlayIntentDeclared } from '../mappers/playerProfileMappers';

export interface PlayIntentDeclaration {
  readonly sport: Sport;
  readonly intent: PlayIntent;
  readonly surface: PlayIntentSurface;
}

/**
 * **What the profile now holds**, and never what was sent.
 *
 * The route answers with the declaration as recorded, and that is the value a caller may put
 * in a cache — the same discipline the week write runs, where the response carries the week
 * in the platform's reading order. Echoing the request back would make every write
 * self-confirming, which is the one shape a cache cannot be corrected out of.
 *
 * `undefined` where the answer names a sport or an intent this build cannot read: there is
 * nothing honest to record, and re-reading is the caller's remedy.
 */
export function declarePlayIntent(
  declaration: PlayIntentDeclaration,
): Promise<{ readonly sport: Sport; readonly intent: PlayIntent } | undefined> {
  return putPlayIntent({
    wireSport: toWireSport(declaration.sport),
    intent: declaration.intent,
    surface: declaration.surface,
  }).then(toPlayIntentDeclared);
}
