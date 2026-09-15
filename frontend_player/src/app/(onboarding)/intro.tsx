/** Step two of onboarding's second part. See `tags.tsx` for the rule this obeys. */

import { Redirect } from 'expo-router';

import { SocialIntroStep, useSocialStepAdmission } from '@/features/player_profile/types';

export default function IntroRoute() {
  const admission = useSocialStepAdmission('intro');

  if (admission === 'start-over') return <Redirect href="/tags" />;

  return <SocialIntroStep />;
}
