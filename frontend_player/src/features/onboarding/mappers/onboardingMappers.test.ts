/**
 * The wire boundary, in both directions.
 *
 * Fixtures are typed from the generated schema on purpose: a backend shape change then
 * fails `pnpm typecheck` rather than failing here with a confusing assertion.
 */

import type { Wire } from "@/test-support/transport";

import {
  toAssessmentRun,
  toAssessmentStep,
  toSkillRatings,
  toSport,
  toSports,
  toWireSport,
} from "./onboardingMappers";

const RATING: Wire["RatingResponse"] = {
  sport: "PADEL",
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: "Established", lower: 2.7, upper: 3.8 },
  status: "initial_estimate",
  engine_version: "racketskill-v3",
  updated_at: "2026-08-14T09:00:00Z",
};

describe("sports", () => {
  it("translates the wire's spelling to the app's, and back", () => {
    expect(toSport("BADMINTON")).toBe("badminton");
    expect(toWireSport("badminton")).toBe("BADMINTON");
  });

  it("drops a sport this build has no identity for", () => {
    // The generated union says this cannot arrive. A phone that has not updated in eight
    // months says otherwise, and a sport with no name and no colour is a card that cannot
    // be drawn — so it is dropped rather than guessed at.
    expect(toSport("PICKLEBALL")).toBeUndefined();

    const served: Wire["SportsResponse"] = {
      sports: [
        { sport: "TENNIS", players: 2, durations: [60, 90] },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any -- see above: the
        // point of the case is a value the contract says is impossible.
        { sport: "PICKLEBALL" as any, players: 4, durations: [60] },
      ],
    };

    expect(toSports(served)).toEqual(["tennis"]);
  });
});

describe("ratings", () => {
  it("reads mu and sigma as Level and Uncertainty, and takes the band as sent", () => {
    const [rating] = toSkillRatings({ ratings: [RATING] });

    expect(rating).toEqual({
      sport: "padel",
      level: 2.71,
      uncertainty: 0.62,
      confidence: 28,
      range: { low: 2.09, high: 3.33 },
      // Band edges are deliberately uneven and were wrong once already. They come from
      // the response; nothing in this client restates them.
      band: { name: "Established", lower: 2.7, upper: 3.8 },
      status: "initial_estimate",
      engineVersion: "racketskill-v3",
      updatedAt: "2026-08-14T09:00:00Z",
    });
  });

  it("reads an unrated player as an empty list, not as a failure", () => {
    expect(toSkillRatings({ ratings: [] })).toEqual([]);
  });
});

describe("assessment steps", () => {
  const QUESTION: Wire["QuestionResponse"] = {
    id: "q-regularity",
    category: "Recent activity",
    tier: null,
    situation: "Think about the last three months",
    text: "How often do you play?",
    qualifier: "A normal month, not your busiest",
    options: [{ id: "weekly", text: "About once a week" }],
  };

  it("maps the outstanding question, with the wire's null tier as absent", () => {
    const step = toAssessmentStep({
      assessment_id: "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6",
      status: "in_progress",
      questions_asked: 0,
      question: QUESTION,
    });

    expect(step.assessmentId).toBe("1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6");
    expect(step.question?.category).toBe("Recent activity");
    expect(step.question?.tier).toBeUndefined();
    expect(step.question?.options).toEqual([{ id: "weekly", text: "About once a week" }]);
  });

  it("carries the answers already behind the run, without counting the outstanding one", () => {
    // The count is the server's, taken as sent. A run four answers in reports 4 while
    // holding a fifth question — the screen is what adds the one, not this.
    const resumed = toAssessmentStep({
      assessment_id: "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6",
      status: "in_progress",
      questions_asked: 4,
      question: QUESTION,
    });

    expect(resumed.questionsAsked).toBe(4);

    const fresh = toAssessmentStep({
      assessment_id: "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6",
      status: "in_progress",
      questions_asked: 0,
      question: QUESTION,
    });

    expect(fresh.questionsAsked).toBe(0);
  });

  it("has no question when there is nothing outstanding", () => {
    const step = toAssessmentStep({
      assessment_id: "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6",
      status: "completed",
      questions_asked: 2,
      question: null,
    });

    expect(step.question).toBeUndefined();
  });

  it("tells the two terminal states apart", () => {
    // Both arrive with no question, and they demand opposite screens: one produced a
    // rating, the other discarded its answers and produced nothing.
    const abandoned = toAssessmentStep({
      assessment_id: "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6",
      status: "abandoned",
      questions_asked: 2,
      question: null,
    });

    expect(abandoned.status).toBe("abandoned");
    expect(abandoned.question).toBeUndefined();
  });

  it("reads a status it does not recognise as still running", () => {
    // The question is what says whether there is something to answer. A status added to
    // the engine after this build shipped is not grounds for throwing a player out of a
    // run they are half way through.
    const step = toAssessmentStep({
      assessment_id: "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6",
      status: "quarantined_pending_review",
      questions_asked: 1,
      question: QUESTION,
    });

    expect(step.status).toBe("in_progress");
  });

  it("takes the run's sport from the question that was asked, not from the answer", () => {
    // `/assessments/in-progress` is scoped to a sport and the payload does not name one.
    const run = toAssessmentRun(
      {
        assessment_id: "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6",
        status: "in_progress",
        questions_asked: 3,
      },
      "squash",
    );

    expect(run).toEqual({
      assessmentId: "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6",
      sport: "squash",
    });
  });
});
