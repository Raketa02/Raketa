/**
 * The wire boundary: transport shapes in, domain objects out.
 *
 * Two things this file is responsible for beyond renaming fields:
 *
 * 1. **The two spellings of a sport meet here and nowhere else.** The exhaustive
 *    `satisfies Record<...>` on both tables is the mechanism: a fifth sport added to the
 *    backend arrives through `pnpm gen:api` as a new member of the generated union, and
 *    the missing key fails `pnpm typecheck` rather than silently rendering nothing.
 * 2. **A sport this build does not know is dropped, not guessed.** The generated union
 *    says it cannot happen; a phone that has not updated in eight months says otherwise.
 *    A sport with no identity colour and no name is a card that cannot be drawn, so the
 *    picker shows the ones it can and the player rates the rest after updating.
 */

import type { components } from "@/generated/schema";

import type {
  AssessmentRun,
  AssessmentStatus,
  AssessmentStep,
  Question,
} from "../domain/Assessment";
import type { SkillRating } from "../domain/SkillRating";
import type { Sport } from "../domain/Sport";

type WireSport = components["schemas"]["Sport"];
type RatingResponse = components["schemas"]["RatingResponse"];
type RatingsResponse = components["schemas"]["RatingsResponse"];
type SportsResponse = components["schemas"]["SportsResponse"];
type QuestionResponse = components["schemas"]["QuestionResponse"];
type AssessmentStepResponse = components["schemas"]["AssessmentStepResponse"];

const SPORT_BY_WIRE = {
  PADEL: "padel",
  TENNIS: "tennis",
  SQUASH: "squash",
  BADMINTON: "badminton",
} as const satisfies Record<WireSport, Sport>;

const WIRE_BY_SPORT = {
  padel: "PADEL",
  tennis: "TENNIS",
  squash: "SQUASH",
  badminton: "BADMINTON",
} as const satisfies Record<Sport, WireSport>;

/** `undefined` for a sport this build has no identity for — see the note above. */
export function toSport(wire: string): Sport | undefined {
  return Object.hasOwn(SPORT_BY_WIRE, wire)
    ? SPORT_BY_WIRE[wire as WireSport]
    : undefined;
}

export function toWireSport(sport: Sport): WireSport {
  return WIRE_BY_SPORT[sport];
}

export function toSports(response: SportsResponse): readonly Sport[] {
  return response.sports
    .map((served) => toSport(served.sport))
    .filter((sport): sport is Sport => sport !== undefined);
}

/**
 * `mu` and `sigma` become Level and Uncertainty. The wire keeps the engine's spelling so
 * the rating a player was just shown and the rating they read back later are not
 * described in two vocabularies; the app keeps the domain's.
 */
export function toSkillRating(wire: RatingResponse): SkillRating | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;

  return {
    sport,
    level: wire.mu,
    uncertainty: wire.sigma,
    confidence: wire.confidence,
    range: { low: wire.range.low, high: wire.range.high },
    // Straight from the response. Band edges are deliberately uneven and were wrong once
    // already, so nothing in this client restates them.
    band: { name: wire.band.name, lower: wire.band.lower, upper: wire.band.upper },
    status: wire.status,
    engineVersion: wire.engine_version,
    updatedAt: wire.updated_at,
  };
}

export function toSkillRatings(response: RatingsResponse): readonly SkillRating[] {
  return response.ratings
    .map(toSkillRating)
    .filter((rating): rating is SkillRating => rating !== undefined);
}

function toQuestion(wire: QuestionResponse): Question {
  return {
    id: wire.id,
    category: wire.category,
    // `null` is the wire's "no tier"; the app's absent value is `undefined`.
    tier: wire.tier ?? undefined,
    situation: wire.situation,
    text: wire.text,
    qualifier: wire.qualifier,
    options: wire.options.map((option) => ({ id: option.id, text: option.text })),
  };
}

/**
 * `status` is a bare string on the wire, so the narrowing happens here rather than being
 * asserted downstream. Anything this build does not recognise is `in_progress`: the
 * question is what says whether there is something to answer, and an unknown status is
 * not grounds for ending a run the client cannot interpret.
 */
function toStatus(wire: string): AssessmentStatus {
  return wire === "completed" || wire === "abandoned" ? wire : "in_progress";
}

export function toAssessmentStep(wire: AssessmentStepResponse): AssessmentStep {
  return {
    assessmentId: wire.assessment_id,
    status: toStatus(wire.status),
    // Answers behind the run, never including the outstanding question. Carried across as
    // it arrives — the client neither counts nor adjusts it; see `AssessmentStep`.
    questionsAsked: wire.questions_asked,
    question: wire.question == null ? undefined : toQuestion(wire.question),
  };
}

/**
 * A run to resume.
 *
 * The sport comes from the caller, not from the payload: `/assessments/in-progress` is
 * asked one sport at a time, so which sport a run belongs to is known from the question
 * rather than from the answer.
 */
export function toAssessmentRun(
  wire: AssessmentStepResponse,
  sport: Sport,
): AssessmentRun {
  return { assessmentId: wire.assessment_id, sport };
}
