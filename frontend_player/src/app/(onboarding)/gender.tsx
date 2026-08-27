/** Step six of onboarding's second part. See `tags.tsx` for the rule this obeys. */

import { Redirect } from 'expo-router';

import { SocialGenderStep, useSocialStepAdmission } from '@/features/player_profile/types';

export default function GenderRoute() {
  const admission = useSocialStepAdmission('gender');

  if (admission === 'start-over') return <Redirect href="/tags" />;

  return <SocialGenderStep />;
}
