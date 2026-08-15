/**
 * Answer the outstanding question — or change an answer already given — and get back
 * whatever comes next.
 *
 * **One request, and the transcript decides what it means** (ADR-0020). A question the run
 * has not answered is answered; one it has is changed, and every answer after it is
 * discarded; and the option already recorded records nothing at all. There is nothing to
 * choose between here, which is why there is one function: the client names a question and
 * an option, and the server reads the run it already holds.
 *
 * **One round trip.** The response *is* the next question — or a stopped run — so nothing
 * here refetches what the server just handed back, and nothing predicts it: the engine
 * chooses the next question from the whole transcript, which means selecting it is the
 * rating calculation itself. There is no optimistic update available to write, and no
 * offline queue possible, because there is no question five until the server has seen
 * answer four.
 *
 * **A stale-step conflict is recovered here rather than surfaced.** A double-tapped
 * confirm, the same assessment answered on a second device, and a change asked for after
 * the rating already exists all land as a conflict about a run this device is behind on —
 * and none of them is a failure the player can act on, so the honest response is to
 * re-read the step and carry on rather than to tell them something went wrong. Re-reading
 * is also what makes the recovery correct for every shape at once: the refreshed step is
 * the next question if there is one, and a finished run if there is not.
 *
 * The recovery is deliberately *not* a retry. Re-sending the answer would fail identically
 * — the question it names is no longer outstanding — which is why this reads instead of
 * repeating the write.
 */

import { isAppError } from '@/shared/errors';

import { submitAnswer } from '../api/onboardingApi';
import type { AssessmentStep } from '../domain/Assessment';
import { isStaleStepConflict } from '../domain/answerRecovery';
import { toAssessmentStep } from '../mappers/onboardingMappers';

import { fetchAssessment } from './fetchAssessment';

export interface AnswerQuestionCommand {
  readonly assessmentId: string;
  readonly questionId: string;
  readonly optionId: string;
}

export interface AnswerQuestionOptions {
  readonly signal?: AbortSignal;
}

export async function answerQuestion(
  { assessmentId, questionId, optionId }: AnswerQuestionCommand,
  { signal }: AnswerQuestionOptions = {},
): Promise<AssessmentStep> {
  try {
    const step = await submitAnswer(
      assessmentId,
      { question_id: questionId, option_id: optionId },
      { signal },
    );
    return toAssessmentStep(step);
  } catch (error) {
    if (isAppError(error) && isStaleStepConflict(error)) {
      return fetchAssessment(assessmentId, { signal });
    }
    throw error;
  }
}
