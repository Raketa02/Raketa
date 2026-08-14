/**
 * The question route's params are untrusted input — the route is reachable from a deep
 * link, and the assessment id becomes a request path.
 */

import { parseQuestionRouteParams } from "./routeParams";

const ID = "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6";

describe("question route params", () => {
  it("accepts a well-formed link", () => {
    expect(parseQuestionRouteParams({ assessmentId: ID, sport: "padel" })).toEqual({
      assessmentId: ID,
      sport: "padel",
    });
  });

  it("rejects an assessment id that is not one", () => {
    expect(
      parseQuestionRouteParams({ assessmentId: "../../users/me", sport: "padel" }),
    ).toBeUndefined();
  });

  it("rejects a sport outside the closed set", () => {
    expect(
      parseQuestionRouteParams({ assessmentId: ID, sport: "pickleball" }),
    ).toBeUndefined();
  });

  it("rejects a missing param, and the array form expo-router can hand over", () => {
    expect(parseQuestionRouteParams({ assessmentId: ID })).toBeUndefined();
    expect(
      parseQuestionRouteParams({ assessmentId: ID, sport: ["padel", "tennis"] }),
    ).toBeUndefined();
  });
});
