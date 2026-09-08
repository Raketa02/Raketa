/**
 * The Player profile feature's only public surface.
 *
 * `src/app/` and other features import from here and from nowhere else inside this folder —
 * ESLint blocks the deep paths. Anything not re-exported below is an internal detail this
 * feature is free to change.
 *
 * **The feature is the profile, not the flow.** Onboarding's second part is where a profile
 * is first collected, and the profile screen will later edit the same values against the
 * same rules — so the rules, the draft and the steps live here rather than inside
 * `onboarding`, which owns a walk that happens once
 * ([ADR-0089](../../../../docs/adr/0089-player-profile-context-event-sourced.md)).
 */

export { SocialTagsStep } from './components/SocialTagsStep';
export { SocialPhotosStep } from './components/SocialPhotosStep';
export { SocialAvailabilityStep } from './components/SocialAvailabilityStep';
export { SocialLocationStep } from './components/SocialLocationStep';
export { SocialRadiusStep } from './components/SocialRadiusStep';
export { SocialGenderStep } from './components/SocialGenderStep';
export { SocialOptInStep } from './components/SocialOptInStep';

export { SOCIAL_STEPS, type SocialStep } from './domain/socialSteps';
/**
 * Where the second part begins, as a route.
 *
 * The entry gate and the end of onboarding's first part both send a player here, and both
 * used to spell the route themselves. **The first step is the only door in** — the draft is
 * client-held and starts empty, so the middle of the part is not a place anyone can be sent.
 */
export { SOCIAL_STEPS_ENTRY } from './components/socialStepRoutes';
export type {
  AvailabilitySlot,
  LocationArea,
  ProfileDraft,
  ProposalsOptIn,
} from './domain/ProfileDraft';
export type { Gender, GenderPreference } from './domain/gender';

/**
 * Whether a link may drop a player onto a step in the middle of the part. The *decision* is
 * exported, never the redirect: where a player belongs is this feature's rule, and which
 * route expresses it is the routing layer's.
 */
export { useSocialStepAdmission, type SocialStepAdmission } from './hooks/useSocialStepAdmission';

/**
 * Which poster a player id gets — exported because **Play draws other people's**.
 *
 * A candidate with no photograph gets the generated poster on every card in Play, and the
 * design system's contract is that *one player id always produces one poster*: the drawing is
 * `CourtPoster`'s and both sets it chooses from are the theme's, but **which** member of them
 * an id maps to is a feature's, and this is the feature that decided it. A second copy of the
 * hash in `play/` would be two posters for one person the day either copy is touched — which
 * is the drift `Tick` was extracted to prevent, in a place a type could not see it.
 *
 * It is a **re-export rather than a promotion to `shared/`**: `recoveryMessage.ts`'s rule is
 * that the *third copy* is the signal to move something, and there is no second copy. The
 * cross-feature import goes through this surface, which is what this file is for.
 */

/**
 * **The profile surface Play reads, and the two writes beside it.**
 *
 * One read of the week, the radius and the per-sport declaration
 * ([#246](https://github.com/Raketa02/Raketa/issues/246)), and one unkeyed `PUT` per fact.
 * They are this feature's rather than Play's because the writes are:
 * [`the-play-screens.md`](../../../../docs/specs/matchmaking/the-play-screens.md) §0 calls
 * them *"two writes that are not matchmaking's at all"*, and a read whose paired writes live
 * elsewhere is a read in the wrong feature. *You* will draw the same three facts.
 *
 * `useDeclarePlayIntent` is the one-tap interstitial's, which ADR-0094 calls *"permanent, not
 * a migration path"*: a searcher with a rating and no declaration is gated by it, and that is
 * what makes every searcher having declared true rather than intended.
 */
export type { PlayerProfileSurface, PlayIntentDeclarations } from './domain/PlayerProfileSurface';
export type { PlayIntentSurface } from './api/playerProfileApi';
export type { PlayIntentDeclaration } from './use-cases/declarePlayIntent';
export {
  useChangeAvailability,
  useChangeSearchRadius,
  useDeclarePlayIntent,
  useProfileSurface,
} from './hooks/useProfileSurface';

/**
 * **The You tab's first real section** — one row per rated sport, and what each one has
 * declared ([#296](https://github.com/Raketa02/Raketa/issues/296)).
 *
 * Named by `shell`'s `YouScreen` and by nothing else. It is here rather than in `play/` for the
 * reason `PlayerProfileSurface` gives about the read it is drawn from: the three writes are
 * this feature's, and *You* was always going to draw the same three facts. It writes with
 * `PROFILE_SCREEN`, the one value of `PlayIntentSurface` that had no client behind it.
 */
export { PlayIntentsSection } from './components/PlayIntentsSection';

/**
 * The bounds a Search radius is held inside, and the words the figure is read with.
 *
 * Exported because **Play edits the same number against the same rules**, which is this
 * feature's founding argument in the direction it was written for: *"the profile editor will
 * obey these rules from a screen that looks nothing like this one."* The onboarding step was
 * the first such screen and Find a game is the second — the served minimum, maximum, step and
 * default are product's to retune, so a second copy of the snapping anywhere would be a
 * staler one in builds already on phones.
 */
export { useProfileOptions } from './hooks/useProfileOptions';
export {
  openingRadius,
  radiusAtFraction,
  radiusFraction,
  steppedRadius,
  topOfScale,
  type SearchRadiusBounds,
} from './domain/searchRadius';
export {
  RADIUS_LABEL,
  radiusFigure,
  radiusWords,
  spokenRadius,
  widestRadiusFigure,
} from './components/radiusPresentation';

/**
 * The week's two spellings, exported for the weeks Play meets that this feature does not own:
 * the search's `availability_override` on the way out, and the week a raised
 * `KEEP_THESE_TIMES` quotes back on the way in.
 *
 * `sport.ts`'s rule is the shape — *the two spellings meet in `mappers/`, and only there* —
 * so this is a re-export rather than a second table in `play/mappers/`, which would be the
 * drift `week.ts` was promoted to stop arriving one layer lower.
 *
 * **There is no third spelling.** A raised `KEEP_THESE_TIMES` used to carry the week as the
 * joined codes the event stream stores, and this feature owned a `toWeekFromCodes` that split
 * them; the contract now sends the same `AvailabilitySlotResource` every other week on the
 * wire does, so `toWeekCells` reads that one too and no client parses our persistence format
 * ([#286](https://github.com/Raketa02/Raketa/issues/286)).
 */
export { toWeekCells, toWireSlots } from './mappers/playerProfileMappers';
