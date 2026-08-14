/**
 * The result route.
 *
 * Both params are **untrusted input** — this route is reachable from a deep link — and are
 * validated by the same schema the question route uses, for the same reason: the wire does
 * not say which sport a step belongs to, so the sport travels as a param.
 */

import { Redirect, useLocalSearchParams } from "expo-router";

import { ResultScreen, parseAssessmentRouteParams } from "@/features/onboarding/types";

export default function ResultRoute() {
  const params = parseAssessmentRouteParams(useLocalSearchParams());

  if (params === undefined) return <Redirect href="/welcome" />;

  return <ResultScreen assessmentId={params.assessmentId} sport={params.sport} />;
}
