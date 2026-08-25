/** Step five of onboarding's second part. See `tags.tsx` for the rule this obeys. */

import { Redirect } from 'expo-router';

import { SocialStepScreen, useSocialStepAdmission } from '@/features/player_profile/types';

export default function RadiusRoute() {
  const admission = useSocialStepAdmission('radius');

  if (admission === 'start-over') return <Redirect href="/tags" />;

  return <SocialStepScreen step="radius" />;
}
