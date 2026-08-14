/**
 * The onboarding feature's only public surface.
 *
 * `src/app/` and other features import from here and from nowhere else inside this
 * folder — ESLint blocks the deep paths. Anything not re-exported below is an internal
 * detail this feature is free to change.
 */

export { DataScreen } from './components/DataScreen';
export { DoneScreen } from './components/DoneScreen';
export { EntryUnavailableScreen } from './components/EntryUnavailableScreen';
export { QuestionScreen } from './components/QuestionScreen';
export { ResultScreen } from './components/ResultScreen';
export { SportsPickerScreen } from './components/SportsPickerScreen';
export { WelcomeScreen } from './components/WelcomeScreen';

export type { Sport } from './domain/Sport';
export type { SkillRating } from './domain/SkillRating';

export { onboardingKeys } from './hooks/onboardingKeys';

/**
 * The entry gate. The *decision* is exported, never the redirect: where a player belongs
 * is this feature's rule, and which route expresses it is the routing layer's.
 */
export { useEntryDecision, type EntryDecision } from './hooks/useEntryDecision';

/**
 * A walk through onboarding is over when the player is in the app. The gate is the one
 * place that knows they are, so it is the one place that says so — see the hook for why
 * this is the definition rather than a convention.
 */
export { useEndOnboardingPass } from './hooks/useEndOnboardingPass';

/** Route params are untrusted input, so the route that reads them validates them here. */
export { parseAssessmentRouteParams, type AssessmentRouteParams } from './schemas/routeParams';
