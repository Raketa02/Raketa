/**
 * The entry gate's rule, with no renderer and no network.
 *
 * These cases are the whole of "where does a player belong on launch", and each one is a
 * decision someone could plausibly get backwards.
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

/** Nothing set aside — the ordinary launch, and the default for most of these. */
const NONE_DEFERRED: readonly string[] = [];

describe("where a player belongs on launch", () => {
  it("sends a player with no ratings to the welcome screen", () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
      }),
    ).toEqual({ kind: "welcome" });
  });

  it("sends a rated player into the app", () => {
    expect(
      entryDestination({
        ratings: [rating("padel")],
        runInProgress: undefined,
        deferredRunIds: NONE_DEFERRED,
      }),
    ).toEqual({ kind: "app" });
  });

  it("resumes an unfinished run", () => {
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
      }),
    ).toEqual({ kind: "resume", run: RUN });
  });

  it("resumes an unfinished run even when the player is already rated elsewhere", () => {
    // The case the ordering exists for: rated at padel, half way through tennis. Reading
    // ratings first would drop them into the app with those tennis answers stranded, and
    // nothing would ever offer them the rest of the questionnaire.
    expect(
      entryDestination({
        ratings: [rating("padel")],
        runInProgress: RUN,
        deferredRunIds: NONE_DEFERRED,
      }),
    ).toEqual({ kind: "resume", run: RUN });
  });
});

describe("a run the player asked to come back to later", () => {
  it("is not resumed, so leaving the questionnaire is actually leaving it", () => {
    // Without this the exit is not an exit: the run is genuinely still unfinished, so the
    // gate would route straight back to the question the player just left.
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: [RUN.assessmentId],
      }),
    ).toEqual({ kind: "welcome" });
  });

  it("lets a player rated elsewhere reach the app", () => {
    expect(
      entryDestination({
        ratings: [rating("padel")],
        runInProgress: RUN,
        deferredRunIds: [RUN.assessmentId],
      }),
    ).toEqual({ kind: "app" });
  });

  it("does not stand in for a different run", () => {
    // Deferral is about one run, not about onboarding. A tennis run set aside says
    // nothing about the squash run the player started afterwards.
    expect(
      entryDestination({
        ratings: [],
        runInProgress: RUN,
        deferredRunIds: ["a-different-assessment"],
      }),
    ).toEqual({ kind: "resume", run: RUN });
  });
});
