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
 * How a run ended, where it ended at all.
 *
 * The two terminal states are **not interchangeable and demand opposite screens**: a
 * completed run produced a rating, and an abandoned one produced nothing and discarded
 * its answers. Both arrive with no outstanding question, so "no question left" cannot be
 * read as "there is a result" — which is exactly what it meant before abandonment
 * existed.
 *
 * An unrecognised status is treated as `in_progress`: the question is what says whether
 * there is something to answer, and a status this build has never heard of is not
 * grounds for throwing a player out of a run.
 */
export type AssessmentStatus = "in_progress" | "completed" | "abandoned";

/**
 * The server-driven step: what to render next.
 *
 * A step carries a question, or a finished assessment carries none.
 *
 * The wire also carries the result once a run is finished. It is not mapped: **nothing
 * in this slice acts on it**, and a field mapped for a future screen is a field no test
 * covers. The result payload arrives with the result screen (#25).
 */
export interface AssessmentStep {
  readonly assessmentId: string;
  readonly status: AssessmentStatus;
  /**
   * How many of this run's questions have been **answered**.
   *
   * The outstanding `question` is not one of them — it has been put to the player and not
   * answered — so a counter showing which question this is reads this plus one, and a
   * fresh run reports 0. The server replays it from the transcript on every read, which
   * is the whole reason it is here rather than counted on the device: the transcript is
   * the only thing that ever survived a resume, a reinstall or a second handset.
   */
  readonly questionsAsked: number;
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
