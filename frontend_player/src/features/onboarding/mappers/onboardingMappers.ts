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

import type { components } from '@/generated/schema';

import type {
  AssessmentRun,
  AssessmentStatus,
  AssessmentStep,
  Question,
} from '../domain/Assessment';
import type { AssessmentResult } from '../domain/AssessmentResult';
import type { SkillRating } from '../domain/SkillRating';
import type { Sport } from '@/shared/vocabulary/sport';

type WireSport = components['schemas']['Sport'];
type RatingResponse = components['schemas']['RatingResponse'];
type RatingsResponse = components['schemas']['RatingsResponse'];
type SportsResponse = components['schemas']['SportsResponse'];
type QuestionResponse = components['schemas']['QuestionResponse'];
type AssessmentStepResponse = components['schemas']['AssessmentStepResponse'];
type ResultResponse = components['schemas']['ResultResponse'];
type InProgressAssessmentResponse = components['schemas']['InProgressAssessmentResponse'];
type InProgressAssessmentsResponse = components['schemas']['InProgressAssessmentsResponse'];

const SPORT_BY_WIRE = {
  PADEL: 'padel',
  TENNIS: 'tennis',
  SQUASH: 'squash',
  BADMINTON: 'badminton',
} as const satisfies Record<WireSport, Sport>;

const WIRE_BY_SPORT = {
  padel: 'PADEL',
  tennis: 'TENNIS',
  squash: 'SQUASH',
  badminton: 'BADMINTON',
} as const satisfies Record<Sport, WireSport>;

/** `undefined` for a sport this build has no identity for — see the note above. */
export function toSport(wire: string): Sport | undefined {
  return Object.hasOwn(SPORT_BY_WIRE, wire) ? SPORT_BY_WIRE[wire as WireSport] : undefined;
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
  return wire === 'completed' || wire === 'abandoned' ? wire : 'in_progress';
}

/**
 * The finished run's rating and its account of itself.
 *
 * **Everything here is carried across, never interpreted.** `direction`, `key`,
 * `calibration_priority` and `status` stay the engine's own words: the client resolves how
 * to *draw* a key it recognises and falls back for one it does not, which is a decision
 * about presentation. Re-ordering, re-deriving or dropping any of it would make this
 * client's explanation a second opinion about a rating it did not compute.
 *
 * `factors` and `uncertainty_factors` are optional on the wire and absent means empty: a
 * beginner who answered one question has one contribution and no wideners, and that is an
 * ordinary result rather than a missing one.
 *
 * `confidence_ceiling` is nullable and its absence is *not* empty — it is a rating whose
 * engine has been retired, which is the same case that carries no `confidence_reason`. It
 * stays absent all the way to the screens, which then say nothing about a ceiling; a default
 * applied here would be the client's own number wearing the server's clothes.
 */
export function toAssessmentResult(wire: ResultResponse): AssessmentResult {
  return {
    level: wire.mu,
    uncertainty: wire.sigma,
    confidence: wire.confidence,
    // `null` and a field this response predates both mean the same thing to the app, and
    // `undefined` is how the app spells absent.
    confidenceCeiling: wire.confidence_ceiling ?? undefined,
    range: { low: wire.range.low, high: wire.range.high },
    // Straight from the response, like every other band in this file.
    band: { name: wire.band.name, lower: wire.band.lower, upper: wire.band.upper },
    status: wire.status,
    questionsAsked: wire.questions_asked,
    engineVersion: wire.engine_version,
    calibrationPriority: wire.calibration_priority,
    confidenceReason:
      wire.confidence_reason == null
        ? undefined
        : { key: wire.confidence_reason.key, sentence: wire.confidence_reason.sentence },
    contributions: (wire.factors ?? []).map((factor) => ({
      key: factor.key,
      label: factor.label,
      direction: factor.direction,
      level: factor.level,
    })),
    wideners: (wire.uncertainty_factors ?? []).map((widener) => ({
      key: widener.key,
      label: widener.label,
      detail: widener.detail,
      sigmaAdded: widener.sigma_added,
    })),
  };
}

export function toAssessmentStep(wire: AssessmentStepResponse): AssessmentStep {
  return {
    assessmentId: wire.assessment_id,
    status: toStatus(wire.status),
    // Answers behind the run, never including the outstanding question. Carried across as
    // it arrives — the client neither counts nor adjusts it; see `AssessmentStep`.
    questionsAsked: wire.questions_asked,
    /**
     * In the order the server sent them, which is the order they were given — and the
     * order a revision truncates at. Re-sorting or de-duplicating here would be this
     * client holding a second opinion about a run it did not conduct. An answered
     * question carries its own copy, so the same `toQuestion` reads both.
     */
    transcript: wire.transcript.map((entry) => ({
      question: toQuestion(entry.question),
      optionId: entry.option_id,
    })),
    question: wire.question == null ? undefined : toQuestion(wire.question),
    result: wire.result == null ? undefined : toAssessmentResult(wire.result),
  };
}

/**
 * A run to resume. `undefined` for a sport this build has no identity for.
 *
 * The sport now comes from the payload rather than from the caller: the collection form of
 * `/assessments/in-progress` names the sport of each run, which is what lets one request
 * answer for all of them.
 *
 * The drop is the same rule as everywhere else in this file, and here it is load-bearing
 * rather than cosmetic — the resume route validates its sport against `SPORTS` before it
 * renders anything, so a run this build cannot name is a run it cannot route to.
 */
export function toAssessmentRun(wire: InProgressAssessmentResponse): AssessmentRun | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;

  return { assessmentId: wire.assessment_id, sport };
}

/**
 * Every unfinished run, in the order the server sent them.
 *
 * **An empty collection is an answer, not a failure** — and it is the common one. Ordering
 * is the server's: it sends them in sport-registry order, which is `SPORTS`' order, so a
 * caller wanting one run takes the first. Re-sorting here would be a second copy of a rule
 * the contract already states, and two copies are two places for it to drift.
 */
export function toAssessmentRuns(
  response: InProgressAssessmentsResponse,
): readonly AssessmentRun[] {
  return response.assessments
    .map((entry) => toAssessmentRun(entry))
    .filter((run): run is AssessmentRun => run !== undefined);
}
