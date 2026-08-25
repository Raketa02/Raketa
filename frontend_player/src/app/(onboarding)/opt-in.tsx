/** Step six of onboarding's second part. See `tags.tsx` for the rule this obeys. */

import { Redirect } from 'expo-router';

import { SocialStepScreen, useSocialStepAdmission } from '@/features/player_profile/types';

export default function OptInRoute() {
  const admission = useSocialStepAdmission('opt-in');

  if (admission === 'start-over') return <Redirect href="/tags" />;

  return <SocialStepScreen step="opt-in" />;
}
