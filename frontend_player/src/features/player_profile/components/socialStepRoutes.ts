/**
 * Each step's route, as a literal the router's typed hrefs accept.
 *
 * The step names *are* the route segments, so this table is one-to-one by construction — it
 * exists because a template literal is not a typed href, not because there is a second
 * naming scheme to translate between.
 */

import { STEP_THAT_ASKS, type MissingAnswer } from '../domain/profileCommit';
import type { SocialStep } from '../domain/socialSteps';

export const SOCIAL_STEP_PATH = {
  tags: '/tags',
  photos: '/photos',
  availability: '/availability',
  location: '/location',
  radius: '/radius',
  'opt-in': '/opt-in',
} as const satisfies Record<SocialStep, string>;

/**
 * The route of the step that asks for an answer the commit is short of.
 *
 * One call rather than `SOCIAL_STEP_PATH[STEP_THAT_ASKS[answer]]` at the call site: which
 * step asks a question is a rule and which route draws it is this file's, and a screen
 * should have to know neither to send a player back to the right place.
 */
export function pathThatAsks(answer: MissingAnswer): SocialStepPath {
  return SOCIAL_STEP_PATH[STEP_THAT_ASKS[answer]];
}

/** The typed href of any one step. Named so a route file can hold one without widening it. */
export type SocialStepPath = (typeof SOCIAL_STEP_PATH)[SocialStep];

/**
 * **The one door into the part**, as a route.
 *
 * Exported because two things outside this feature send a player to it — the entry gate,
 * and the end of onboarding's first part — and both used to spell `/tags` themselves. Where
 * the second part begins is this feature's to say.
 */
export const SOCIAL_STEPS_ENTRY = SOCIAL_STEP_PATH.tags;
