/**
 * The question and result routes' params are untrusted input — both are reachable from a
 * deep link, and the assessment id becomes a request path.
 */

import { parseAssessmentRouteParams } from "./routeParams";

const ID = "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6";

describe("assessment route params", () => {
  it("accepts a well-formed link", () => {
    expect(parseAssessmentRouteParams({ assessmentId: ID, sport: "padel" })).toEqual({
      assessmentId: ID,
      sport: "padel",
    });
  });

  it("rejects an assessment id that is not one", () => {
    expect(
      parseAssessmentRouteParams({ assessmentId: "../../users/me", sport: "padel" }),
    ).toBeUndefined();
  });

  it("rejects a sport outside the closed set", () => {
    expect(
      parseAssessmentRouteParams({ assessmentId: ID, sport: "pickleball" }),
    ).toBeUndefined();
  });

  it("rejects a missing param, and the array form expo-router can hand over", () => {
    expect(parseAssessmentRouteParams({ assessmentId: ID })).toBeUndefined();
    expect(
      parseAssessmentRouteParams({ assessmentId: ID, sport: ["padel", "tennis"] }),
    ).toBeUndefined();
  });
});
