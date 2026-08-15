/**
 * What a failed answer means, and whether it is a failure at all.
 *
 * Two of the backend's codes say something different from the rest: they do not report
 * that the submission failed, they report that **this device's view of the run is behind
 * the server's**. Answers are append-only and the engine accepts one only for the question
 * it last asked, so both of these arrive from a submission the run has already moved past:
 *
 * - `question_not_outstanding` — a double-tapped confirm, or the same assessment answered
 *   on a second device. The first answer landed; this one describes a question that is no
 *   longer awaiting a response.
 * - `assessment_already_finished` — the run ended in between.
 * - `answer_not_revisable` — the same submission read as a *change* to an answer already
 *   given, on a run whose rating now exists. A rating is proved once and never edited, so
 *   the answers behind it are settled too; what this device is behind on is that the run
 *   finished, which is the same thing `assessment_already_finished` reports from the other
 *   direction.
 *
 * None is anything the player did wrong and none is retryable as sent, so showing any of
 * them as an error would be reporting a failure that did not happen. The recovery is to
 * re-read the step and render whatever is genuinely outstanding — a question where there
 * is one, and a finished run where there is not.
 *
 * **Both are 409s from the same endpoint family**, which is exactly why the backend was
 * corrected to give every error its own code (#18): on status alone they are
 * indistinguishable from a conflict that *is* a failure, and this rule could not be
 * written at all.
 */

import type { AppError } from '@/shared/errors';

const STALE_STEP_CODES: readonly string[] = [
  'question_not_outstanding',
  'assessment_already_finished',
  'answer_not_revisable',
];

/**
 * True when the answer did not fail — the client is simply looking at a step the run has
 * moved past.
 *
 * Keyed on `code` and never on `kind` or `status`: `kind` is `conflict` for every 409, and
 * a code this build has not been taught falls back to its status, so an unrecognised
 * conflict correctly reads as a real failure rather than being silently swallowed.
 */
export function isStaleStepConflict(error: AppError): boolean {
  return error.code !== undefined && STALE_STEP_CODES.includes(error.code);
}
