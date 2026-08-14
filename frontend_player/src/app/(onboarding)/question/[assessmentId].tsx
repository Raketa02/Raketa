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
 */

import { Redirect, useLocalSearchParams } from "expo-router";

import { QuestionScreen, parseAssessmentRouteParams } from "@/features/onboarding/types";

export default function QuestionRoute() {
  const params = parseAssessmentRouteParams(useLocalSearchParams());

  if (params === undefined) return <Redirect href="/welcome" />;

  return <QuestionScreen assessmentId={params.assessmentId} sport={params.sport} />;
}
