/**
 * Step one of onboarding's second part, and the only door into it.
 *
 * The entry gate redirects here, and **every later step sends a stranger back here**: the
 * draft is client-held and starts empty, so a link landing in the middle of the part would
 * let a player commit a Player profile built from screens they never saw. Whether they may
 * be admitted is the feature's rule (`admissionToStep`); turning its answer into a route is
 * all a route file does — which is why the five later steps are this file with one word
 * changed, and why none of them repeats the reasoning.
 *
 * This one needs no redirect branch, because the first step is the answer to being turned
 * away from any of the others.
 */

import { SocialStepScreen, useSocialStepAdmission } from '@/features/player_profile/types';

export default function TagsRoute() {
  useSocialStepAdmission('tags');

  return <SocialStepScreen step="tags" />;
}
