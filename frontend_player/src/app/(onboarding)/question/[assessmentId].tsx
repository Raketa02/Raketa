/**
 * The question route.
 *
 * Both params are **untrusted input** — this route is reachable from a deep link, and the
 * assessment id becomes a request path. They are validated before anything reads them,
 * and a link that does not survive validation lands on welcome rather than issuing a
 * request built from someone else's string.
 *
 * The sport travels as a param because the wire does not carry it: `/assessments/{id}`
 * answers with a step, and which sport that step belongs to is known from the question
 * that was asked, not from the answer.
 *
 * **Surviving validation is not the same as belonging here.** A well-formed link naming a
 * sport this player never chose is still not a way into the middle of onboarding — a pass has
 * two doors, the picker and the Skill passport's *Add a sport*, and a link is neither. Whether
 * a player may be admitted is the feature's rule; turning its answer into a route is this
 * file's whole job.
 */

import { Redirect, useLocalSearchParams } from 'expo-router';

import {
  QuestionScreen,
  parseAssessmentRouteParams,
  useOnboardingAdmission,
} from '@/features/onboarding/types';

export default function QuestionRoute() {
  const params = parseAssessmentRouteParams(useLocalSearchParams());
  // Before the guard below, because a hook may not be conditional. It tolerates the
  // absent sport a rejected link leaves behind.
  const admission = useOnboardingAdmission(params?.sport);

  if (params === undefined || admission === 'start-over') return <Redirect href="/welcome" />;

  // `at` says where the player starts standing, which is what an entry on the review opens.
  // Absent is the ordinary case and means *wherever the run stands*.
  return <QuestionScreen assessmentId={params.assessmentId} sport={params.sport} at={params.at} />;
}
