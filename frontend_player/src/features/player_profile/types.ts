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
export { COURT_POSTER_COUNT, courtPosterFor } from './components/courtPosterFraming';
