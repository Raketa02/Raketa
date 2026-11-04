/**
 * The result route.
 *
 * Both params are **untrusted input** — this route is reachable from a deep link — and are
 * validated by the same schema the question route uses, for the same reason: the wire does
 * not say which sport a step belongs to, so the sport travels as a param.
 *
 * It carries the same admission rule as the question route, and for the same reason: a
 * result is a screen *inside* the questionnaire, so a link naming a sport this player never
 * chose belongs on Home rather than at somebody's rating.
 *
 * **A pass begun on a group names it on the way back** (#729, ADR-0200 §3): the last control says
 * *Back to {group name}*, and the name is the groups feature's read — which imports onboarding at
 * runtime, so onboarding cannot import it back. This file asks both: the group the pass returns to, and its name.
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import { useGroupName } from '@/features/groups/types';
import {
  ResultScreen,
  parseAssessmentRouteParams,
  useOnboardingAdmission,
  useReturningGroup,
} from '@/features/onboarding/types';

export default function ResultRoute() {
  const params = parseAssessmentRouteParams(useLocalSearchParams());
  const admission = useOnboardingAdmission(params?.sport);
  const groupName = useGroupName(useReturningGroup());

  if (params === undefined || admission === 'start-over') return <Redirect href="/" />;

  return (
    <ResultScreen
      assessmentId={params.assessmentId}
      sport={params.sport}
      {...(groupName === undefined ? {} : { groupName })}
    />
  );
}
