/**
 * The rule that decides whether a failed submission failed at all.
 *
 * Pure — no renderer, no cache, no network. The codes it recognises are the whole reason
 * #18 gave every backend error its own code: on status alone they are one 409 among many,
 * and this rule could not tell them from a conflict that really is a failure.
 */

import { AppError } from '@/shared/errors';

import { isStaleStepConflict } from './answerRecovery';

/** A conflict as the error mapper builds one: same status, different code. */
function conflict(code: string): AppError {
  return new AppError('conflict', 'business-conflict', 'Conflict.', { code, status: 409 });
}

describe('a stale-step conflict', () => {
  it('recognises the double-tapped confirm and the second device', () => {
    expect(isStaleStepConflict(conflict('question_not_outstanding'))).toBe(true);
  });

  it('recognises a run that finished in between', () => {
    expect(isStaleStepConflict(conflict('assessment_already_finished'))).toBe(true);
  });

  it('recognises a change asked for after the rating already existed', () => {
    // The revision's own refusal. Nothing was recorded, but there is nothing to record
    // either — the rating is proved and the answers behind it are settled — so the honest
    // response is to re-read and show the player what their run actually is now.
    expect(isStaleStepConflict(conflict('answer_not_revisable'))).toBe(true);
  });

  it('recognises a rating asked for on a run that was not sitting at the stop', () => {
    // Completion's own refusal, and it answers for two runs: one still holding a question,
    // and one abandoned somewhere else. Both are this device being behind, and one
    // re-read renders whichever it turns out to be.
    expect(isStaleStepConflict(conflict('assessment_not_stopped'))).toBe(true);
  });

  it('does not swallow another conflict on the same status', () => {
    // `kind` and `status` are identical to the two above. Only the code separates them,
    // and a rule keyed on either of the other two would silently recover from a failure
    // that genuinely needs reporting.
    expect(isStaleStepConflict(conflict('invalid_answer_option'))).toBe(false);
  });

  it('does not swallow a code this build has never been taught', () => {
    // An unrecognised code falls back to its status in the error mapper, so it arrives
    // here looking like any other conflict. Guessing that a new code means "already
    // handled" would hide a real failure on every phone that has not updated.
    expect(isStaleStepConflict(conflict('some_code_added_next_year'))).toBe(false);
  });

  it('does not swallow a failure that never reached the server', () => {
    expect(
      isStaleStepConflict(
        new AppError('network-unavailable', 'retryable-automatically', 'Offline.'),
      ),
    ).toBe(false);
  });
});
