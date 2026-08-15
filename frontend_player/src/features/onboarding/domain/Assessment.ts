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

import type { AssessmentResult } from './AssessmentResult';
import type { Sport } from './Sport';

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
 * One question already answered: the question **as it was asked**, and what was chosen.
 *
 * The copy is carried rather than referenced because the server is the only thing that
 * ever held it. A run resumed after a reinstall, or picked up on a second handset, has
 * nothing on the device to render an answered question from — which is why the transcript
 * is served on every step instead of accumulated as the player answers.
 */
export interface AnsweredQuestion {
  readonly question: Question;
  readonly optionId: string;
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
export type AssessmentStatus = 'in_progress' | 'completed' | 'abandoned';

/**
 * The server-driven step: what to render next.
 *
 * A step carries a question, or a finished assessment carries a result. **Neither is
 * guaranteed**: an abandoned run has ended with no question left and nothing to show, and
 * reading "no question" as "there is a result" is what would announce a rating to a player
 * who stopped rating that sport.
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
  /**
   * Every answer given so far, in the order they were given — the run's whole past, on
   * every read.
   *
   * **Empty, never absent, and never remembered.** It is replayed from the stream on each
   * response, so it survives a resume, a reinstall and a second handset; and a client that
   * counted what it had itself shown would be wrong in the one direction it could not
   * detect, because a revision makes the transcript *shorter* than the one before it.
   * Its length is `questionsAsked`; the outstanding `question` is not in it.
   */
  readonly transcript: readonly AnsweredQuestion[];
  readonly question: Question | undefined;
  /** The rating this run produced, once it has produced one. */
  readonly result: AssessmentResult | undefined;
}

/**
 * A run the player has left unfinished, as the entry gate sees it.
 *
 * The assessment id and its sport, and nothing else: this is what a router needs. The
 * outstanding question is deliberately absent — the gate decides *where* to send the
 * player, and the run it routes to is re-read there.
 */
export interface AssessmentRun {
  readonly assessmentId: string;
  readonly sport: Sport;
}
