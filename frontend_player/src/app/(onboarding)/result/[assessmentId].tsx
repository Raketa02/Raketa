/**
 * The result route.
 *
 * Both params are **untrusted input** — this route is reachable from a deep link — and are
 * validated by the same schema the question route uses, for the same reason: the wire does
 * not say which sport a step belongs to, so the sport travels as a param.
 *
 * It carries the same admission rule as the question route, and for the same reason: a
 * result is a screen *inside* onboarding, so a link naming a sport this player never chose
 * belongs at the beginning rather than at somebody's rating.
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import {
  ResultScreen,
  parseAssessmentRouteParams,
  useOnboardingAdmission,
} from '@/features/onboarding/types';

export default function ResultRoute() {
  const params = parseAssessmentRouteParams(useLocalSearchParams());
  const admission = useOnboardingAdmission(params?.sport);

  if (params === undefined || admission === 'start-over') return <Redirect href="/welcome" />;

  return <ResultScreen assessmentId={params.assessmentId} sport={params.sport} />;
}
