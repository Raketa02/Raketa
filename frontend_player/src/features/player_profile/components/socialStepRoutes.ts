/**
 * Each step's route, as a literal the router's typed hrefs accept.
 *
 * The step names *are* the route segments, so this table is one-to-one by construction — it
 * exists because a template literal is not a typed href, not because there is a second
 * naming scheme to translate between.
 */

import type { SocialStep } from '../domain/socialSteps';

export const SOCIAL_STEP_PATH = {
  tags: '/tags',
  photos: '/photos',
  availability: '/availability',
  location: '/location',
  radius: '/radius',
  'opt-in': '/opt-in',
} as const satisfies Record<SocialStep, string>;
