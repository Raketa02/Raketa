/**
 * The three profile facts a Play screen reads, in one round trip.
 *
 * `GET /api/v1/players/me/profile` carries the availability grid, the Search radius and the
 * per-sport Play intent, across the two aggregates that own them
 * ([#246](https://github.com/Raketa02/Raketa/issues/246)). It is **not the whole profile**:
 * gender and the gender preference are a standing refusal, and tags, photos and the location
 * area are a deferral this same route grows when *You* is built. Neither absence is
 * representable here, which is the point — this type is what the route serves, and a field
 * appears the day the route serves one.
 *
 * ## Why this lives in `player_profile` and not in `play`
 *
 * Play is the only reader today, and it would have been the easier home. It loses to the
 * **writes**: `PUT /players/me/availability`, `PUT /players/me/search-radius` and
 * `PUT /play-intents/{sport}` are *"two writes that are not matchmaking's at all"*
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §0), and
 * a read whose three paired writes live in another feature is a read in the wrong feature.
 * *You* will draw the same three facts from the same route.
 *
 * ## The one vocabulary this feature does not own
 *
 * `PlayIntent` is `shared/vocabulary/playIntent`'s. It began in `features/play/domain/` and
 * moved the day this feature became the second to hold one — a Play intent is a root-glossary
 * term rather than either feature's reading of one, which is the ownership test `sport.ts` and
 * `week.ts` were promoted under. Reaching it through Play's public surface instead would have
 * made this mapper import a feature whose own surface exports a screen built out of this one.
 */

import type { PlayIntent } from '@/shared/vocabulary/playIntent';
import type { Sport } from '@/shared/vocabulary/sport';
import type { WeekCell } from '@/shared/vocabulary/week';

/**
 * What was **declared**, per sport — and absence means *undeclared*, never `NO_PREFERENCE`.
 *
 * ADR-0094 forbids a null intent on the wire, so the map holds only the sports a player has
 * answered for. *Rated but undeclared* is therefore a set difference against `GET /ratings`,
 * which is what lets the search screen open the one-tap interstitial **before** a search is
 * refused with `play_intent_not_declared` rather than after it.
 */
export type PlayIntentDeclarations = Readonly<Partial<Record<Sport, PlayIntent>>>;

export interface PlayerProfileSurface {
  /**
   * The cells this player has ticked, in the platform's own reading order.
   *
   * **An empty week is a real answer** — a player may clear theirs — and it means *we do not
   * know when they play*, never *never*. It is what Play's working copy is seeded from and
   * what *changed from your profile* is compared against.
   */
  readonly week: readonly WeekCell[];
  /** Whole kilometres. What the search screen's slider opens at. */
  readonly searchRadiusKm: number;
  readonly playIntents: PlayIntentDeclarations;
}
