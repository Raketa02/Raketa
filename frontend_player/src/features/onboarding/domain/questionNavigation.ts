/**
 * Where a player is standing in a run, and what is drawn there.
 *
 * A run's questions are positions 1..n: the served transcript's answers in the order they
 * were given, and then — while the questionnaire is still asking — the outstanding
 * question one past the last of them. Moving over the answered ones is free, because the
 * whole run arrives with every step; nothing here reads the network and nothing here
 * records anything (ADR-0020).
 *
 * **Position is derived from the transcript on every read, never accumulated.** A revision
 * truncates the transcript, so the run can describe *less* progress than the read before
 * it — and a client holding its own count would be wrong in exactly the direction it could
 * not detect. That is also why `standingPosition` clamps: a player standing on question
 * eight when the run shortens to three is pulled to the end of what still exists rather
 * than left looking at a question that no longer does.
 */

import type { AnsweredQuestion, AssessmentStep, Question } from './Assessment';

/** A question the player is looking at, and the answer recorded for it if there is one. */
export interface StandingQuestion {
  readonly position: number;
  readonly question: Question;
  /** The option they chose, where this question has been answered. */
  readonly answer: string | undefined;
}

/**
 * The position of the question the run is waiting on: one past its last answer.
 *
 * It is a position even when nothing is outstanding. A stopped questionnaire has answered
 * every question it drew, so the player standing "at the end" is standing one past them —
 * which is the position with no question at it.
 */
export function outstandingPosition(step: AssessmentStep | undefined): number {
  return (step?.transcript.length ?? 0) + 1;
}

/**
 * Where the player stands, given where they last moved to.
 *
 * `undefined` means they have not moved: they follow the end of the run, which is what
 * keeps a player who answers a question on the question that answer produced.
 */
export function standingPosition(
  step: AssessmentStep | undefined,
  movedTo: number | undefined,
): number {
  const end = outstandingPosition(step);
  if (movedTo === undefined) return end;
  return Math.min(Math.max(movedTo, 1), end);
}

/**
 * The question at a 1-based position: an answered one from the transcript, or the
 * outstanding one at the end.
 *
 * `undefined` where the run has nothing to show at that position — the end of a
 * questionnaire that has stopped, or a run still loading.
 */
export function questionAt(
  step: AssessmentStep | undefined,
  position: number,
): StandingQuestion | undefined {
  if (step === undefined) return undefined;

  const answered: AnsweredQuestion | undefined = step.transcript[position - 1];
  if (answered !== undefined) {
    return { position, question: answered.question, answer: answered.optionId };
  }

  if (position === outstandingPosition(step) && step.question !== undefined) {
    return { position, question: step.question, answer: undefined };
  }

  return undefined;
}
