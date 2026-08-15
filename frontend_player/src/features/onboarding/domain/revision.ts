/**
 * Changing an answer already given: whether a tap is a change at all, and what it costs.
 *
 * **A revision truncates.** Every answer after the changed one is discarded, because each
 * was pitched at a difficulty chosen from the estimate as it then stood — so an answer
 * that outlived a change to an earlier one would mean something the player never said
 * ([ADR-0020](../../../../../docs/adr/0020-revisable-assessment-answers.md)). The number
 * of answers that go is not a detail of the request: it is the thing the player is told
 * *before* the change happens rather than discovering afterwards.
 *
 * **Re-selecting the option already recorded is not a revision.** The server records
 * nothing for it, so changing your mind and changing it back costs nothing — and a
 * confirmation put in front of a player who has changed nothing is a consequence
 * announced for an act that will not occur. Both halves are one rule here rather than two
 * conditions in a screen, because they are one question: what does choosing this option,
 * here, mean?
 *
 * Nothing here reads the network. The whole run arrives with every step, so the cost of a
 * change is knowable before anything is sent.
 */

import type { AssessmentStep } from './Assessment';

/** A change the player has asked for, before it is confirmed or sent. */
export interface ProposedRevision {
  readonly questionId: string;
  /** The option they want instead. Never the one already recorded — see below. */
  readonly optionId: string;
  /**
   * How many later answers the change discards.
   *
   * **Zero on the most recent answer**, which is an ordinary case rather than a
   * degenerate one: no other answer is lost, and the questions the engine asks next may
   * still differ, because it is asked them from the transcript this change produces.
   */
  readonly discards: number;
}

/**
 * What choosing `optionId` at `position` means.
 *
 * `undefined` where it means nothing at all: the option already recorded there, or a
 * position the run holds no answer at — the outstanding question is *answered*, never
 * revised, and a position past the end of a truncated transcript belongs to nobody.
 */
export function proposeRevision(
  step: AssessmentStep | undefined,
  position: number,
  optionId: string,
): ProposedRevision | undefined {
  if (step === undefined) return undefined;

  const answered = step.transcript[position - 1];
  if (answered === undefined) return undefined;
  if (answered.optionId === optionId) return undefined;

  return {
    questionId: answered.question.id,
    optionId,
    // Everything after this position, and never this position itself: the answer here is
    // replaced rather than discarded.
    discards: step.transcript.length - position,
  };
}
