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
export { SocialIntroStep } from './components/SocialIntroStep';
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
export type { WeeklyHour, LocationArea, ProfileDraft, ProposalsOptIn } from './domain/ProfileDraft';
export type { Gender, GenderPreference } from './domain/gender';

/**
 * Whether a link may drop a player onto a step in the middle of the part. The *decision* is
 * exported, never the redirect: where a player belongs is this feature's rule, and which
 * route expresses it is the routing layer's.
 */
export { useSocialStepAdmission, type SocialStepAdmission } from './hooks/useSocialStepAdmission';

/**
 * **The one-tap declaration's write** — the Games deck's interstitial asks it
 * ([ADR-0094](../../../../docs/adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md): *"permanent,
 * not a migration path"*). The profile surface's read and its other writes were Play's too,
 * until the old loop was removed ([#576](https://github.com/Raketa02/Raketa/issues/576)); You
 * reads and writes them inside this feature.
 */
export type { PlayIntentSurface } from './api/playerProfileApi';
export { useDeclarePlayIntent } from './hooks/useProfileSurface';

/**
 * **The location moves on a cold start** — silently, after a day in the background, never on
 * a plain foreground ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6). Called by the `(app)` layout with the entry gate's own answer, because that is the
 * branch that knows a player is signed in and past onboarding; the feature owns the read, the
 * coarsening and the write, and the layout owns nothing but the moment.
 */
export { useLocationRefresh } from './hooks/useLocationRefresh';

/**
 * **This feature's rows on the You tab, and the screens behind them**
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1–§2). The shell composes the tab and names the rows; the route files under
 * `(app)/(tabs)/you/` name the screens. Each row is a title, a live line off the read that
 * carries the fact, and a door; each screen is the onboarding step's control under the tab's
 * chrome with a *Save* — the week, the radius, the tags, the intro, each of the two gender
 * groups — or written on every change to the row — the photos — or on every press — the
 * opt-in — or the section as built, behind a row.
 *
 * `PlayIntentsSection` ([#296](https://github.com/Raketa02/Raketa/issues/296)) is drawn by
 * `WhatKindOfGameScreen` and stays internal; `AreaUpdatesNote` moved into *Where you play*
 * ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6), and its sentence `AREA_UPDATES_LINE` is exported for the suites that hold the tab to
 * its words, as the rows' words are.
 */
export {
  GameSuggestionsRow,
  HowFarToLookRow,
  IntroRow,
  PhotosRow,
  TagsRow,
  WhatKindOfGameRow,
  WhereYouPlayRow,
  WhoYouPlayWithRow,
  YourWeekRow,
  type YouRowProps,
} from './components/YouRows';
export { YourWeekScreen } from './components/YourWeekScreen';
export { HowFarToLookScreen } from './components/HowFarToLookScreen';
export { WhereYouPlayScreen } from './components/WhereYouPlayScreen';
export { WhatKindOfGameScreen } from './components/WhatKindOfGameScreen';
export { PhotosScreen } from './components/PhotosScreen';
export { TagsScreen } from './components/TagsScreen';
export { IntroScreen } from './components/IntroScreen';
export { WhoYouPlayWithScreen } from './components/WhoYouPlayWithScreen';
export { GameSuggestionsScreen } from './components/GameSuggestionsScreen';
export { AREA_UPDATES_LINE } from './components/locationPresentation';
export {
  AREA_LINE,
  AREA_SET,
  CLEAR_ALL,
  GAME_SUGGESTIONS_TITLE,
  HOW_FAR_TO_LOOK_TITLE,
  INTRO_TITLE,
  KIND_OF_GAME_LINE,
  PHOTOS_TITLE,
  READ_AGAIN,
  REMOVE_INTRO,
  SAVE,
  SAVED,
  SAVE_YOUR_WEEK,
  TAGS_TITLE,
  WHAT_KIND_OF_GAME_TITLE,
  WHERE_YOU_PLAY_TITLE,
  WHO_YOU_PLAY_WITH_TITLE,
  YOUR_WEEK_TITLE,
  gameSuggestionsLine,
  introLine,
  kindOfGameLine,
  photosLine,
  radiusLine,
  tagsLine,
  weekLine,
  whoYouPlayWithLine,
} from './components/youProfilePresentation';
