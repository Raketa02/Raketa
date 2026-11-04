/**
 * **The door where play begins** — what it offers a player rated in nothing
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §2, §5,
 * [#730](https://github.com/Raketa02/Raketa/issues/730)).
 *
 * Onboarding no longer asks for a level, so it is asked where one unlocks something: a player
 * group's Games, Fill in and Friends, *Post a game* and Members. The door offers one of two things,
 * and which is a rule rather than a screen's business, because every host draws the same door:
 *
 * - **the picker**, *Which sports do you play?*, over every sport and with nothing ticked — for a
 *   player with nothing left halfway;
 * - **the run she left**, at the question she is on — *Carry on with your padel questions — you're
 *   on question 5*. **Leaving halfway never takes over the app** (§5): the entry gate has no resume
 *   branch, and this door is the only thing that offers the run again. It never offers to start
 *   over, because the run's answers are on the server and it resumes where it stands
 *   (ADR-0019, ADR-0020).
 *
 * **The question she is on is the run's own count**, replayed from its transcript on every read:
 * the answered questions plus the one outstanding. A run whose questions have stopped has none
 * outstanding — every answer is in and the review is next — and she is still on the last one she
 * answered. A run the list called unfinished and its own read calls completed or abandoned ended
 * in between, on another phone, and there is nothing to carry on.
 */

import type { AssessmentRun, AssessmentStep } from './Assessment';
import { runStanding } from './runStanding';

export type DoorOffer =
  /** The sports picker, over every sport, nothing ticked. */
  | { readonly kind: 'start' }
  /** The run left halfway — `question` is 1-based, the one she is on. */
  | { readonly kind: 'carry-on'; readonly run: AssessmentRun; readonly question: number };

/**
 * @param run the first unfinished run, in the server's order — `undefined` for none.
 * @param step that run's own read, for where it stands — `undefined` where it could not be read,
 * which offers the picker: starting a sport with an unfinished run hands that run back.
 */
export function levelDoor(
  run: AssessmentRun | undefined,
  step: AssessmentStep | undefined,
): DoorOffer {
  if (run === undefined || step === undefined) return { kind: 'start' };
  switch (runStanding(step)) {
    case 'asking':
      return { kind: 'carry-on', run, question: step.questionsAsked + 1 };
    case 'stopped':
      return { kind: 'carry-on', run, question: step.questionsAsked };
    default:
      return { kind: 'start' };
  }
}
