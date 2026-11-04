/**
 * The words the **end of the part** says: what finishing does, what is still wanted, and
 * what to do when it did not land.
 *
 * ## Why these are not in `genderPresentation`
 *
 * They are shown on the same screen — *Who you play with* is the last step and carries the
 * finish ([#582](https://github.com/Raketa02/Raketa/issues/582)) — and they are about a
 * different thing. Nothing below is about who a player is or who they play with: it describes
 * the state of a setup flow, it is shown conditionally, and it would say the same words on
 * whichever step happened to end the part. That is how it moved here once already, from the
 * proposals question that used to be last, without one sentence changing.
 *
 * ## What is deliberately not said
 *
 * Nothing here claims the account is set up. A failure says the commit did not land and
 * offers the control that failed; the moment setting up is actually finished, the player is
 * already on the closing screens. A message that congratulated a player on a write that did
 * not happen is the one thing this screen must never do.
 */

import type { AppError } from '@/shared/errors';

import { introRefusal } from '../domain/intro';
import {
  ASKED_ON_THE_LAST_STEP,
  STEP_THAT_ASKS,
  type AnswerAskedBehind,
  type MissingAnswer,
} from '../domain/profileCommit';
import type { SocialStep } from '../domain/socialSteps';

import { CHANGE_INTRO_LABEL, introRefusalSentence } from './introPresentation';

/**
 * The finish itself — **the act, and nothing promised past it.** It used to name what was on
 * the other side (*show me players*); the Players deck that promise pointed at is gone, and
 * what follows the commit is Home (#730).
 */
export const FINISH_LABEL = 'Finish';

/** What the finish promises, once there is something for it to promise. */
export const FINISH_HINT = 'Sends everything you answered and finishes setting up';

/** While the request is in flight. The control keeps its place and stops taking presses. */
export const FINISHING_WORD = 'Finishing…';

/**
 * The heading over a failed commit.
 *
 * It names what did not happen rather than what went wrong — the sentence underneath is
 * `recoveryMessage`'s job, and it is the same one every other failure in the app uses.
 */
export const COMMIT_FAILED_TITLE = "That didn't go through";

/**
 * Said under the recovery sentence, and it is the load-bearing half.
 *
 * A player who has just answered six screens and seen a failure has one question, and it is
 * not *what went wrong*. Nothing was lost, and pressing again is safe — the retry carries
 * the same key as the attempt that failed, so it cannot produce a second profile.
 */
export const COMMIT_FAILED_BODY =
  'Nothing you answered was lost. Try again — this can only ever set you up once.';

/**
 * A photo has not finished arriving.
 *
 * The photos step lets a player continue while an upload is in flight, deliberately — the
 * upload outlives the screen so that pressing continue does not cancel it. The commit is
 * where that has to be waited for: the body names photos by the ids the server gave back,
 * so one sent now would quietly leave out a picture the player watched upload.
 *
 * **It asks for nothing**, because there is nothing to ask for. It resolves itself.
 */
export const UPLOADING_TITLE = 'One moment — a photo is still arriving';
export const UPLOADING_BODY =
  'Finishing now would leave it out, so we are waiting for it. Nothing else is holding this up.';
export const UPLOADING_HINT = 'Waiting for a photo to finish uploading';

/** An answer the commit still needs, and the words that ask for it. */
export interface MissingAnswerCopy {
  readonly title: string;
  readonly body: string;
  /** The control that goes back to the step that asks it. */
  readonly label: string;
  /** Why the finish is closed, for whoever cannot see that it is. */
  readonly finishHint: string;
}

/**
 * What the last step says about each answer it cannot finish without.
 *
 * **The week is here because ADR-0102 made it an answer rather than a blank.** It is the
 * one entry a player can reach by going forward rather than by skipping: the availability
 * step will not continue on an empty grid, so an unticked week at the end means the draft
 * was carried past that step some other way — a build from before the floor, a restored
 * draft — and the honest thing is to name the step and offer the way back to it.
 *
 * **The area is the one a player actually meets.** The location step can be left with none —
 * it names that cost on the control that leaves it, and this is where the cost is
 * collected: search and matchmaking have one spatial input, and a profile without it takes
 * part in neither. The step insists here rather than earlier because being trapped on step
 * five behind an OS prompt is not a setup flow; being asked once more at the end, with the
 * way back one press away, is.
 *
 * **The gender answer has no entry**: it is asked on this very screen, so what is missing is
 * not a step to go back to but the three controls above the finish. That is
 * `genderPresentation`'s hint, and it stays there with the rest of the step's words.
 */
export const MISSING_ANSWER_COPY: Readonly<Record<AnswerAskedBehind, MissingAnswerCopy>> = {
  availability: {
    title: 'We still need your ordinary week',
    body: 'One hour of the week is enough. Without any there is nothing to compare with another player’s week — and a week nobody gave is never read as never free, so we would rather ask than guess it.',
    label: 'Set when you usually play',
    finishHint: 'Set when you usually play to finish',
  },
  location: {
    title: 'We still need the area you play in',
    body: 'Finding players near you works from one thing: roughly where you play. Without it there is nowhere to search from and no one to match you with, so this is the one answer setting up cannot finish without.',
    label: 'Set the area you play in',
    finishHint: 'Set the area you play in to finish',
  },
};

/** An outstanding answer, and its words. The pair, so no caller has to re-derive one. */
export interface AnswerStillWanted {
  readonly answer: AnswerAskedBehind;
  readonly copy: MissingAnswerCopy;
}

/**
 * Which answer the last step should ask for, or `undefined` when the only one outstanding
 * is the question that step itself asks.
 *
 * **The first entry, because `missing` is in step order** — so a player short of two answers
 * is sent to the earlier one and finds the later one on the way back rather than being
 * bounced twice. The answer travels with its words so the control that goes back and the
 * sentence explaining why cannot end up naming two different steps.
 */
export function answerStillWanted(
  missing: readonly MissingAnswer[],
): AnswerStillWanted | undefined {
  const answer = missing.find(
    (candidate): candidate is AnswerAskedBehind => candidate !== ASKED_ON_THE_LAST_STEP,
  );
  return answer === undefined ? undefined : { answer, copy: MISSING_ANSWER_COPY[answer] };
}

/**
 * The commit's refusals that name an answer a step asks for.
 *
 * **The feature's own `code` table**, which is the half `recoveryMessage` deliberately
 * leaves to whoever owns the endpoint: a recovery category can say *check the details above
 * and try again*, and a screen with five steps behind it has to say **which** detail and
 * offer the way back.
 *
 * It is keyed by the wire code and never by the message — the message is a diagnostic the
 * backend writes for a log, and branching on it would ship English into every locale and
 * let a copy edit on the server change what an installed app does.
 *
 * One entry today. It is a table rather than an `if` because the commit has several refusals
 * and the others will want their own sentences the moment a screen can produce one. The
 * intro's refusal is **not** in it, and that is the point of the next function: nothing is
 * missing when a line is refused, so it is not an answer still wanted and does not take
 * those words.
 */
const ANSWER_THE_COMMIT_REFUSED: Readonly<Record<string, AnswerAskedBehind>> = {
  weekly_hours_empty: 'availability',
};

/**
 * A refusal the commit made that a step can fix: where to go, what to say, and the control
 * that goes there.
 *
 * One shape for two kinds of refusal — an answer the server found missing, and a line the
 * server would not admit — because the last step draws both the same way: the sentence in
 * the failure note, and a `secondary` control under it back to the step. What differs is
 * where the words come from, and that is decided here rather than on the screen.
 */
export interface CommitRefusal {
  readonly step: SocialStep;
  /** What to change, said in the failure note in place of *try again*. */
  readonly body: string;
  /** The control that goes back to the step. */
  readonly label: string;
}

/**
 * Which step a failed commit sends the player back to, if it names one.
 *
 * **The commit re-validates what the picker already enforced**, exactly as it does for
 * tags: a disabled button is absent from a replayed request and from an older build, so
 * `weekly_hours_empty` is reachable even though the availability step will not
 * continue without a tick. When it arrives, *try again* is the wrong sentence — retrying the
 * same body fails identically — so the screen asks for the answer and offers the step that
 * takes it, in the same words as an answer the draft is short of. Which side noticed is not
 * the player's to care about.
 *
 * **`intro_not_admitted` is the other kind.** Nothing is missing: the line is there and the
 * server will not keep it, for one coarse reason it names and one pattern it does not. The
 * sentence is the reason's, from `introPresentation`, and the way back is the intro step. A
 * reason this build has no words for still names the step — the code is recognised even
 * where the detail is not — and says the gap.
 */
export function stepTheCommitRefused(error: AppError): CommitRefusal | undefined {
  if (error.code === undefined) return undefined;

  const answer = ANSWER_THE_COMMIT_REFUSED[error.code];
  if (answer !== undefined) {
    const copy = MISSING_ANSWER_COPY[answer];
    return { step: STEP_THAT_ASKS[answer], body: copy.body, label: copy.label };
  }

  const intro = introRefusal(error);
  if (intro !== undefined) {
    return {
      step: 'intro',
      body: introRefusalSentence(intro.reason),
      label: CHANGE_INTRO_LABEL,
    };
  }

  return undefined;
}
