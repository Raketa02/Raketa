/**
 * What a step says the run is doing — the four readings, in one place.
 *
 * A step carries a status and, at most, one of a question and a result. **At most**, not
 * exactly one: since the questionnaire's stop and the assessment's completion became two
 * moments ([ADR-0020](../../../../../docs/adr/0020-revisable-assessment-answers.md)),
 * *neither* is an ordinary state a live run sits in, and the status is what tells it from
 * the other run that has neither.
 *
 * | status        | question | result | means                                      |
 * | ------------- | -------- | ------ | ------------------------------------------ |
 * | `in_progress` | yes      | —      | the questionnaire, awaiting that answer    |
 * | `in_progress` | —        | —      | **stopped**: nothing left to ask, no rating |
 * | `completed`   | —        | yes    | the rating exists                          |
 * | `abandoned`   | —        | —      | the run ended without one                  |
 *
 * **This is a rule, not a screen's business, because two screens read it and must not
 * disagree.** The questionnaire routes to the review when it stops; the review routes back
 * to the questionnaire when there is a question again. Two copies of the reading would be
 * two screens each certain the other one is where the player belongs — which is a loop,
 * and the kind that only appears on a real device.
 *
 * Before the stop existed, *no question left* could only mean *there is a result*. Reading
 * it that way now shows a player who has answered everything a result screen with no
 * result on it.
 */

import type { AssessmentStep } from './Assessment';

/**
 * - `asking` — a question is outstanding.
 * - `stopped` — the questionnaire has stopped and nothing has been rated. Every answer is
 *   still revisable, and completing is what creates the Skill rating.
 * - `rated` — the run produced a Skill rating, and its answers are settled.
 * - `ended` — abandoned. No question, no rating, and nothing to say about it.
 */
export type RunStanding = 'asking' | 'stopped' | 'rated' | 'ended';

/** `undefined` while there is no step yet — a run still loading is not a state to route on. */
export function runStanding(step: AssessmentStep | undefined): RunStanding | undefined {
  if (step === undefined) return undefined;
  if (step.status === 'abandoned') return 'ended';
  if (step.status === 'completed') return 'rated';
  // In progress, however this build read the status: the question is what says whether
  // there is something to answer, and a status this build has never heard of is not
  // grounds for throwing a player out of a run (see `toStatus`).
  return step.question === undefined ? 'stopped' : 'asking';
}
