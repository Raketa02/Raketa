/**
 * The review route.
 *
 * Both params are **untrusted input** — this route is reachable from a deep link — and are
 * validated by the same schema the question and result routes use, for the same reason: the
 * wire does not say which sport a step belongs to, so the sport travels as a param.
 *
 * It carries the same admission rule as the other two, and for the same reason: the review
 * is a screen *inside* onboarding, so a link naming a sport this player never chose belongs
 * at the beginning rather than one control away from creating a rating.
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import {
  ReviewScreen,
  parseAssessmentRouteParams,
  useOnboardingAdmission,
} from '@/features/onboarding/types';

export default function ReviewRoute() {
  const params = parseAssessmentRouteParams(useLocalSearchParams());
  const admission = useOnboardingAdmission(params?.sport);

  if (params === undefined || admission === 'start-over') return <Redirect href="/welcome" />;

  return <ReviewScreen assessmentId={params.assessmentId} sport={params.sport} />;
}
