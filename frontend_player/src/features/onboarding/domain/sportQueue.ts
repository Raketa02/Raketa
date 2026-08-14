/**
 * The sport queue: which sports this player chose to rate, and in what order.
 *
 * It exists only to order the next few assessments and is **never persisted** — not to
 * the server and not to the device. A sport not rated today can be rated any time later,
 * and nothing about a queue survives the run it was made for.
 *
 * The rules live here rather than in the store so they can be tested without one.
 */

import type { Sport } from "./Sport";

/**
 * Add or remove a sport, preserving the order they were chosen in.
 *
 * Choice order is the queue order: the first sport tapped is the first assessment. That
 * is the only meaning the order carries, and appending rather than re-sorting is what
 * keeps it true.
 */
export function toggleSport(queue: readonly Sport[], sport: Sport): readonly Sport[] {
  return queue.includes(sport) ? queue.filter((s) => s !== sport) : [...queue, sport];
}

export interface RatingPosition {
  /** 1-based: the sport being rated right now. */
  readonly index: number;
  readonly total: number;
}

/**
 * Where one sport sits in the queue — the only denominator the progress bar may use.
 *
 * Question count is unknowable by design (the engine stops when one more answer would no
 * longer move the Band), so sports are the one thing the player actually chose and the
 * one honest thing to measure.
 *
 * A sport that is not in the queue is its own run of one. That is the resumed case: the
 * queue was never persisted, so a player returning to an unfinished padel assessment is
 * rating exactly one sport as far as anyone can now know.
 */
export function ratingPosition(
  queue: readonly Sport[],
  sport: Sport,
): RatingPosition {
  const at = queue.indexOf(sport);
  return at === -1 ? { index: 1, total: 1 } : { index: at + 1, total: queue.length };
}
