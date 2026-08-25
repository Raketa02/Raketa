/**
 * The words the **end of the part** says: what finishing does, what is still wanted, and
 * what to do when it did not land.
 *
 * ## Why these are not in `optInPresentation`
 *
 * They are shown on the same screen, and they are a different kind of string. The consent
 * card's sentences are **evidence** — they are stamped with a version because what a player
 * agreed to is the wording they were shown, and re-wording one is a new version with the old
 * one retained. Nothing below is part of any agreement: it describes the state of a setup
 * flow, it is shown conditionally, and improving a sentence here changes what nobody
 * consented to. Putting it in the pinned file would either freeze copy that has no business
 * being frozen, or blur what the version identifier names.
 *
 * This is the file the note about the commit not existing yet was always going to become.
 *
 * ## What is deliberately not said
 *
 * Nothing here claims the account is set up. A failure says the commit did not land and
 * offers the control that failed; the moment setting up is actually finished, the player is
 * already on the closing screens. A message that congratulated a player on a write that did
 * not happen is the one thing this screen must never do.
 */

import type { MissingAnswer } from '../domain/profileCommit';

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
 * **The area is the one a player actually meets.** The location step can be left with none —
 * it names that cost on the control that leaves it, and this is where the cost is
 * collected: search and matchmaking have one spatial input, and a profile without it takes
 * part in neither. The step insists here rather than earlier because being trapped on step
 * four behind an OS prompt is not a setup flow; being asked once more at the end, with the
 * way back one press away, is.
 *
 * The radius is here for completeness rather than because a player can reach it: the radius
 * step writes the served default into the draft the moment it knows it, so an unanswered
 * radius means that step was never reached at all. It gets a real sentence anyway, because a
 * screen that only handles the case somebody predicted is a screen with a blank state.
 *
 * The proposals question has no entry: it is asked on this very screen, so what is missing
 * is not a step to go back to but the two controls immediately above the finish. That is
 * `optInPresentation`'s hint, and it stays there with the rest of the consent copy.
 */
export const MISSING_ANSWER_COPY: Readonly<
  Record<Exclude<MissingAnswer, 'proposals-opt-in'>, MissingAnswerCopy>
> = {
  location: {
    title: 'We still need the area you play in',
    body: 'Finding players near you works from one thing: roughly where you play. Without it there is nowhere to search from and no one to match you with, so this is the one answer setting up cannot finish without.',
    label: 'Set the area you play in',
    finishHint: 'Set the area you play in to finish',
  },
  'search-radius': {
    title: 'We still need how far you will travel',
    body: 'How far out to look is what turns your area into a set of players. Setting up finishes once you have chosen a distance.',
    label: 'Set how far you will travel',
    finishHint: 'Set how far you will travel to finish',
  },
};

/** An outstanding answer, and its words. The pair, so no caller has to re-derive one. */
export interface AnswerStillWanted {
  readonly answer: Exclude<MissingAnswer, 'proposals-opt-in'>;
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
    (candidate): candidate is Exclude<MissingAnswer, 'proposals-opt-in'> =>
      candidate !== 'proposals-opt-in',
  );
  return answer === undefined ? undefined : { answer, copy: MISSING_ANSWER_COPY[answer] };
}
