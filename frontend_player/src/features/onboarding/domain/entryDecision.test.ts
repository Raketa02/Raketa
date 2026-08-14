/**
 * The entry gate's rule, with no renderer and no network.
 *
 * These four cases are the whole of "where does a player belong on launch", and each one
 * is a decision someone could plausibly get backwards.
 */

import type { AssessmentRun } from "./Assessment";
import { entryDestination } from "./entryDecision";
import type { SkillRating } from "./SkillRating";
import type { Sport } from "./Sport";

function rating(sport: Sport): SkillRating {
  return {
    sport,
    level: 2.71,
    uncertainty: 0.62,
    confidence: 28,
    range: { low: 2.09, high: 3.33 },
    band: { name: "Established", lower: 2.7, upper: 3.8 },
    status: "initial_estimate",
    engineVersion: "racketskill-v3",
    updatedAt: "2026-08-14T09:00:00Z",
  };
}

const RUN: AssessmentRun = {
  assessmentId: "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6",
  sport: "tennis",
};

describe("where a player belongs on launch", () => {
  it("sends a player with no ratings to the welcome screen", () => {
    expect(entryDestination({ ratings: [], runInProgress: undefined })).toEqual({
      kind: "welcome",
    });
  });

  it("sends a rated player into the app", () => {
    expect(
      entryDestination({ ratings: [rating("padel")], runInProgress: undefined }),
    ).toEqual({ kind: "app" });
  });

  it("resumes an unfinished run", () => {
    expect(entryDestination({ ratings: [], runInProgress: RUN })).toEqual({
      kind: "resume",
      run: RUN,
    });
  });

  it("resumes an unfinished run even when the player is already rated elsewhere", () => {
    // The case the ordering exists for: rated at padel, half way through tennis. Reading
    // ratings first would drop them into the app with those tennis answers stranded, and
    // nothing would ever offer them the rest of the questionnaire.
    expect(
      entryDestination({ ratings: [rating("padel")], runInProgress: RUN }),
    ).toEqual({ kind: "resume", run: RUN });
  });
});
