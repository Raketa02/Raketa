/** Step two of onboarding's second part. See `tags.tsx` for the rule this obeys. */

import { Redirect } from 'expo-router';

import { SocialStepScreen, useSocialStepAdmission } from '@/features/player_profile/types';

export default function PhotosRoute() {
  const admission = useSocialStepAdmission('photos');

  if (admission === 'start-over') return <Redirect href="/tags" />;

  return <SocialStepScreen step="photos" />;
}
