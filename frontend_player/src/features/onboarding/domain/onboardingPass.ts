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

import type { Sport } from '@/shared/vocabulary/sport';

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
 *
 * **This operates on a queue, not on a pass, because the picker's selection is not one.**
 * A player still choosing has not begun anything — they can add and remove sports and walk
 * away — and modelling that as a pass is what made "no pass" and "a pass someone left
 * half-built" the same value.
 */
export function toggleSport(queue: readonly Sport[], sport: Sport): readonly Sport[] {
  return queue.includes(sport) ? queue.filter((chosen) => chosen !== sport) : [...queue, sport];
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
 * **Nothing, when there is no pass or the sport is not in it.** There is no honest
 * position for a sport nobody chose — and rather than draw a bar with no denominator, the
 * question and result routes turn that player away entirely (`admissionTo` below). So no
 * screen reaches the empty answer today; it stays because it is the honest one, and
 * because it is *why* those routes can send the player back to the beginning.
 *
 * This used to return `{index: 1, total: 1}` for a sport outside the pass. That fallback
 * is what made a resumed run read "Rating 1 of 1" *and* what made a resumed run after a
 * completed pass read "Rating 2 of 2": with the earlier pass never ended, the sport was
 * still in its queue and the fallback never fired. Beginning and ending a pass is what
 * lets it go — a resumed run is now a genuine pass of one sport and reports one of one
 * honestly, through the ordinary rule.
 */
export function positionOf(
  pass: OnboardingPass | undefined,
  sport: Sport,
): RatingPosition | undefined {
  if (pass === undefined) return undefined;
  const at = pass.queue.indexOf(sport);
  return at === -1 ? undefined : { index: at + 1, total: pass.queue.length };
}

export type PassAdmission =
  /** This sport is in the pass that is running. Render the questionnaire. */
  | { readonly kind: 'admit' }
  /** No pass is running: a run reached on its own is a pass of that one sport. */
  | { readonly kind: 'begin' }
  /** A pass is running and this sport is not in it. Onboarding starts at the start. */
  | { readonly kind: 'start-over' };

/**
 * Whether a player may be dropped straight into this sport's questionnaire.
 *
 * **Onboarding happens once, at the beginning.** There is no re-take from inside the app
 * yet, so the only legitimate ways onto a question are the picker's queue and the entry
 * gate resuming an unfinished run. A link that lands somewhere else — a hand-built URL, a
 * stale notification, an invitation forwarded to a player who never chose these sports —
 * is not a shortcut into the middle of a flow, and treating it as one is what produced a
 * questionnaire with no honest progress to show.
 *
 * The three answers are the three real situations:
 *
 * - **No pass** is the resume path. The gate redirects to an outstanding question with no
 *   picker in between, and that run is a genuine pass of one sport.
 * - **The sport is in the pass** is the ordinary case, every screen after the picker.
 * - **A pass is running without this sport** cannot be reached by any flow the app has.
 *   The player goes back to the beginning, and if the run really was theirs the picker
 *   hands it straight back — starting a sport with an unfinished run returns that run.
 *
 * `start-over` must not send the player through the entry gate. The gate answers *resume*
 * for an outstanding run, which would redirect to this same question and ask this same
 * question again — a loop. Welcome is a screen, and it is also literally where onboarding
 * begins.
 */
export function admissionTo(pass: OnboardingPass | undefined, sport: Sport): PassAdmission {
  if (pass === undefined) return { kind: 'begin' };
  return pass.queue.includes(sport) ? { kind: 'admit' } : { kind: 'start-over' };
}

export type PassDestination =
  /** The next sport the player chose. */
  | { readonly kind: 'rate'; readonly sport: Sport }
  /**
   * The summary of what this pass produced — *your starting ratings*.
   *
   * **It is the end of the first part, not the end of onboarding.** What follows it is the
   * done screen's to decide, because that is where the fact it turns on — whether this
   * player still owes a Player profile — is read. This rule's job stops at *is there
   * anything to account for*.
   */
  | { readonly kind: 'closing' }
  /** Straight into the app. */
  | { readonly kind: 'app' };

/**
 * Where a player who **stops before the end of the queue** goes.
 *
 * Named on its own because it is asked twice — by a player pressing *done for now* with
 * sports still to go, and by `nextDestination` when there are none left — and one rule
 * answering both is what stops the two from drifting into different answers to *is there
 * anything to account for*.
 *
 * Two answers, and the question is only ever the one this pass can answer by itself:
 *
 * - **Nothing rated in this pass → the app**, and the entry gate answers from there. There
 *   is no account to give, and this pass knows nothing about ratings an earlier walk made
 *   or about a part left unfinished; the gate knows both. Answering *stop* with screens
 *   about a walk that produced nothing would be the wrong response to what was asked.
 * - **Anything rated → the summary.** The ratings this walk produced are what the player
 *   just earned, and they see them at the moment they finish earning them.
 *
 * **Whether a Player profile is still owed is no longer read here.** It used to be: a
 * player without one was sent into the second part and shown their ratings only after the
 * commit, on the theory that the summary should follow the write that completes the
 * account. That put six more questions between a player and the number they had just spent
 * a minute per sport producing. The summary now comes first for everybody, and the done
 * screen is where the second part is entered from — one screen further on, where the
 * profile fact is read once and acted on once.
 */
export function stopDestination(pass: OnboardingPass | undefined): PassDestination {
  if (pass === undefined || pass.rated.length === 0) return { kind: 'app' };
  return { kind: 'closing' };
}

/**
 * Where the player goes once this sport is dealt with, however it was dealt with.
 *
 * **Finished and abandoned land in the same place**, which is why one rule answers for
 * both. Abandoning is the player saying stop, and it is still the end of that sport: if
 * any sport in the pass was rated, they leave the way the player who finished does — to the
 * summary of what this walk produced. Ending on an abandonment is not a reason to be told
 * none of that.
 *
 * **When the pass produced nothing, it goes straight to the app.** There is no account to
 * give, the done screen has only its empty state to show, and answering *stop* with two
 * more screens would be the wrong response to what the player just asked for. That branch
 * was an array length inside a screen callback until this module existed.
 *
 * **No pass at all is the same answer as a pass that produced nothing**, and for the same
 * reason: there is nothing to account for. This is what sends a player who abandons a
 * resumed run into the app rather than to a summary of the ratings an *earlier* walk
 * produced — that walk ended when they reached the app, and its ratings went with it.
 */
export function nextDestination(pass: OnboardingPass | undefined, sport: Sport): PassDestination {
  if (pass === undefined) return { kind: 'app' };

  const at = pass.queue.indexOf(sport);
  const next = at === -1 ? undefined : pass.queue[at + 1];

  if (next !== undefined) return { kind: 'rate', sport: next };
  return stopDestination(pass);
}
