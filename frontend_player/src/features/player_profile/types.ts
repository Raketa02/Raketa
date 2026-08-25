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
/** The four steps still standing in for themselves. Each ticket removes one from the union. */
export { SocialStepScreen, type UnbuiltSocialStep } from './components/SocialStepScreen';

export { SOCIAL_STEPS, type SocialStep } from './domain/socialSteps';
export type {
  AvailabilitySlot,
  DayPart,
  LocationArea,
  ProfileDraft,
  ProposalsOptIn,
  Weekday,
} from './domain/ProfileDraft';

/**
 * Whether a link may drop a player onto a step in the middle of the part. The *decision* is
 * exported, never the redirect: where a player belongs is this feature's rule, and which
 * route expresses it is the routing layer's.
 */
export { useSocialStepAdmission, type SocialStepAdmission } from './hooks/useSocialStepAdmission';
