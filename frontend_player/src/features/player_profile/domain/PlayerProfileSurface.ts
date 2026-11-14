/**
 * The profile facts the You tab reads and edits, in one round trip.
 *
 * `GET /api/v1/players/me/profile` carries the weekly hours and the per-sport Play intent,
 * across the two aggregates that own them
 * ([#246](https://github.com/Raketa02/Raketa/issues/246)) — and, since the route grew for
 * *You* ([#466](https://github.com/Raketa02/Raketa/issues/466), ADR-0179 §4, §8), the Social
 * tags, the photos with their verdicts and the intro
 * ([#471](https://github.com/Raketa02/Raketa/issues/471)), and the owner's own gender and
 * preference ([#472](https://github.com/Raketa02/Raketa/issues/472)), and *Show me to new people*
 * ([#799](https://github.com/Raketa02/Raketa/issues/799), which replaced #778's *Show me in
 * General*). The Search radius and
 * the proposals answer left it with the old loop
 * ([#581](https://github.com/Raketa02/Raketa/issues/581)). There is no `has_location`,
 * because a profile cannot be committed without an area. This type is what the route serves
 * and this client reads, and a field appears the day both are true.
 *
 * ## Why this lives in `player_profile` and not in `play`
 *
 * Play was its first reader, and it would have been the easier home. It lost to the
 * **writes**: `PUT /players/me/weekly-hours` and `PUT /play-intents/{sport}` are writes that
 * are not matchmaking's at all, and a read whose paired writes live in another feature is a
 * read in the wrong feature. *You* draws the same facts from the same route.
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
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { Sport } from '@/shared/vocabulary/sport';
import type { WeeklyHour } from '@/shared/vocabulary/week';

import type { Gender, GenderPreference } from './gender';
import type { UploadedPhoto } from './photoCollection';

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
  readonly week: readonly WeeklyHour[];
  readonly playIntents: PlayIntentDeclarations;
  /**
   * The Social tags this player holds, **in the vocabulary's order** whatever order the
   * picker sent them in — required at commit, so never empty. A served id this build has no
   * words for is dropped on the way in, as the options are.
   */
  readonly socialTagIds: readonly SocialTagId[];
  /**
   * The photographs in the player's order — the first is the profile photo — each with the
   * verdict the check concluded, or none where nobody looked. **An empty list is a real
   * answer**: a profile may hold none, and the poster stands in.
   */
  readonly photos: readonly UploadedPhoto[];
  /** The line this player wrote about themselves, or absent where none was written. Never `''`. */
  readonly intro?: string;
  /**
   * The owner's own answer to the gender question — served on this one shape and on no other
   * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
   * §4), because a screen that asks it with nothing pre-selected is a screen a player cannot
   * trust. **Absent on a profile committed before the question existed**, and never read as
   * `prefer-not-to-say`, which is an answer somebody gives: the screen pre-selects nothing.
   */
  readonly gender?: Gender;
  /** Who the owner is willing to be matched with. Always present: `any` is what nothing narrowed means. */
  readonly genderPreference: GenderPreference;
  /**
   * ***Show me to new people*** — on, anybody may open the owner's record and ask them; off, only
   * people they share a group, a game or a friendship with
   * ([ADR-0204](../../../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
   * §2, [#799](https://github.com/Raketa02/Raketa/issues/799)). **Always present, and on by
   * default** — a player who had turned *Show me in General* off starts with it off.
   */
  readonly showMeToNewPeople: boolean;
}
