/**
 * The **onboarding pass**: one walk through onboarding, from the sports the player chose
 * to the ratings that walk produced.
 *
 * The app has named this in prose since the flow existed — "this run", "this pass" — and
 * has never modelled it. It was three stores with no owner and the rules that read them
 * inside two screens, which is how "which sport is this, of how many" and "where does the
 * player go after this one" came to have no seam below a mounted screen.
 *
 * ## What a pass is
 *
 * **The sports chosen, in the order chosen, and which of them produced a Skill rating.**
 * Those two facts answer every question onboarding asks about itself: the progress bar's
 * numerator and denominator, which sport comes next, and whether there is anything to
 * account for on the way out.
 *
 * ## What a pass is not
 *
 * **It is not a server concept and must not become one.** An Assessment is per sport; the
 * *sequence* of them is a decision the player made on the picker and nothing on the
 * backend records it. There is no onboarded player either — a rating is per sport, so a
 * player can be rated at padel and unrated at tennis indefinitely.
 *
 * **It does not hold a rating.** `rated` carries identifiers only. Every number a rating
 * is made of belongs to TanStack Query, and a copy here would be a second answer to what
 * this player is rated at, one of which would be stale (docs/architecture.md Part 8).
 *
 * **It does not hold Deferred runs.** A deferral's lifetime is the app session; a pass
 * ends when the player reaches the app. See `store/deferredRuns.store`, which says why
 * folding the two together would send a player straight back into the run they set aside.
 *
 * ## Why the rules live here
 *
 * Every rule below is a decision someone could plausibly get backwards, and none of them
 * needs React, a store or a router to be wrong. Prior art is `entryDecision` — the whole
 * entry gate as a pure function, tested without mounting anything.
 */

import type { Sport } from './Sport';

/** A run that produced a Skill rating. **Identifiers only** — see above. */
export interface RatedRun {
  readonly assessmentId: string;
  readonly sport: Sport;
}

export interface OnboardingPass {
  /**
   * The sports chosen, in the order they were chosen.
   *
   * Choice order is queue order: the first sport tapped is the first assessment, and that
   * is the only meaning the order carries. **The queue is not edited as sports are dealt
   * with** — a sport that was abandoned was still chosen, so it keeps its place. Removing
   * it would renumber the progress bar underneath the player and turn "Rating 2 of 2"
   * into "Rating 1 of 1" as a reward for giving up on the first one.
   */
  readonly queue: readonly Sport[];
  /** The runs that produced a rating, in the order they produced one. */
  readonly rated: readonly RatedRun[];
}

/**
 * A pass over the sports chosen, with nothing rated yet.
 *
 * A *new* queue is a new pass: whatever an earlier walk produced belongs to that walk,
 * and the closing screens account for this one.
 */
export function begin(queue: readonly Sport[]): OnboardingPass {
  return { queue, rated: [] };
}

/**
 * Add or remove a sport, preserving the order they were chosen in.
 *
 * Appending rather than re-sorting is what keeps choice order true.
 */
export function toggleSport(pass: OnboardingPass, sport: Sport): OnboardingPass {
  return {
    ...pass,
    queue: pass.queue.includes(sport)
      ? pass.queue.filter((chosen) => chosen !== sport)
      : [...pass.queue, sport],
  };
}

/**
 * Record that a run produced a rating.
 *
 * **Idempotent, and returning the same pass is the point.** The result screen records
 * what it is showing, and it shows it again on every refetch and every remount — so a
 * second recording must be neither a second card nor a re-render.
 */
export function recordRated(pass: OnboardingPass, run: RatedRun): OnboardingPass {
  return pass.rated.some((done) => done.assessmentId === run.assessmentId)
    ? pass
    : { ...pass, rated: [...pass.rated, run] };
}

export interface RatingPosition {
  /** 1-based: the sport being rated right now. */
  readonly index: number;
  readonly total: number;
}

/**
 * Where one sport sits in the pass — the only denominator the progress bar may use.
 *
 * Question count is unknowable by design (the engine stops when one more answer would no
 * longer move the Band), so sports are the one thing the player actually chose and the
 * one honest thing to measure.
 *
 * A sport outside the pass is reported as its own run of one. **That fallback is a lie
 * this slice deliberately keeps**: it is how a resumed run reads "Rating 1 of 1" today,
 * and it is also how a resumed run after a completed pass reads "Rating 2 of 2". Removing
 * it needs a pass to begin explicitly, which is #47's — this module changes no behaviour.
 */
export function positionOf(pass: OnboardingPass, sport: Sport): RatingPosition {
  const at = pass.queue.indexOf(sport);
  return at === -1 ? { index: 1, total: 1 } : { index: at + 1, total: pass.queue.length };
}

export type PassDestination =
  /** The next sport the player chose. */
  | { readonly kind: 'rate'; readonly sport: Sport }
  /** The closing screens: the summary of what this pass produced, then what is kept. */
  | { readonly kind: 'closing' }
  /** Straight into the app. */
  | { readonly kind: 'app' };

/**
 * Where the player goes once this sport is dealt with, however it was dealt with.
 *
 * **Finished and abandoned land in the same place**, which is why one rule answers for
 * both. Abandoning is the player saying stop, and it is still the end of that sport: if
 * any sport in the pass was rated, they leave through the same closing screens as the
 * player who finished — the done screen accounts for the ratings they made, and the data
 * screen says what was kept and that no one can hand-edit a Level. Ending on an
 * abandonment is not a reason to be told none of that.
 *
 * **When the pass produced nothing, it goes straight to the app.** There is no account to
 * give, the done screen has only its empty state to show, and answering *stop* with two
 * more screens would be the wrong response to what the player just asked for. That branch
 * was an array length inside a screen callback until this module existed.
 */
export function nextDestination(pass: OnboardingPass, sport: Sport): PassDestination {
  const at = pass.queue.indexOf(sport);
  const next = at === -1 ? undefined : pass.queue[at + 1];

  if (next !== undefined) return { kind: 'rate', sport: next };
  return pass.rated.length > 0 ? { kind: 'closing' } : { kind: 'app' };
}
