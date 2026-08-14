/**
 * An assessment: one run of the questionnaire, for one sport.
 *
 * The engine is conversational but **stateless** — it takes the whole transcript on every
 * call and holds nothing between them, which is what lets an assessment's event stream
 * reproduce exactly the questions asked. So the outstanding question *is* the response to
 * the last answer, and this app never predicts it: there are no optimistic updates in
 * this flow, and there is no offline queue, because there is no question five until the
 * server has seen answer four.
 */

import type { Sport } from "./Sport";

export interface AnswerOption {
  readonly id: string;
  readonly text: string;
}

/**
 * A question in its reading order: category, situation, question, answers.
 *
 * The **category** is the screen heading — the question is never the page title, because
 * a title is read last on a screen the eye scans top-down.
 */
export interface Question {
  readonly id: string;
  readonly category: string;
  /** basic / standard / discriminating, where the engine supplies one. */
  readonly tier: string | undefined;
  readonly situation: string;
  readonly text: string;
  /** "A normal match against players at your level" — what the answer should describe. */
  readonly qualifier: string;
  readonly options: readonly AnswerOption[];
}

/**
 * The server-driven step: what to render next.
 *
 * A step carries a question, or a finished assessment carries none.
 *
 * The wire also carries a status and, once finished, a result. Neither is mapped yet:
 * **nothing in this slice acts on them**, and a field mapped for a future screen is a
 * field no test covers. The result payload arrives with the result screen (#25); the
 * status arrives with the abandonment flow (#27), which is the first thing that has to
 * tell an abandoned run from a completed one.
 */
export interface AssessmentStep {
  readonly assessmentId: string;
  readonly question: Question | undefined;
}

/**
 * A run the player has left unfinished, as the entry gate sees it.
 *
 * The sport is **not** on the wire — `GET /assessments/in-progress` is asked one sport at
 * a time, so the sport is known from the question rather than from the answer.
 */
export interface AssessmentRun {
  readonly assessmentId: string;
  readonly sport: Sport;
}
