/** Step three of onboarding's second part. See `tags.tsx` for the rule this obeys. */

import { Redirect } from 'expo-router';

import { SocialAvailabilityStep, useSocialStepAdmission } from '@/features/player_profile/types';

export default function AvailabilityRoute() {
  const admission = useSocialStepAdmission('availability');

  if (admission === 'start-over') return <Redirect href="/tags" />;

  return <SocialAvailabilityStep />;
}
