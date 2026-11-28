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
 * **The sports chosen, in the order chosen, which of them produced a Skill rating — and
 * where the pass began.** The first two facts answer every question the questionnaire asks
 * about itself: the eyebrow's numerator and denominator, which sport comes next, and which sport
 * the way back stands on. The third answers where the way out leads: a pass has an **origin** —
 * a group's tab, Home, or the Skill passport's *Add a sport* — and where it ends is read off it
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3, amended by [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §5). Everything between the two ends is the same walk.
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
 * **It does not hold a run left halfway.** That is the server's, read by the door where play
 * begins and offered as *Carry on* (ADR-0200 §5); nothing resumes a run on launch any more, so
 * nothing on the device remembers one was set aside.
 *
 * ## Why the rules live here
 *
 * Every rule below is a decision someone could plausibly get backwards, and none of them
 * needs React, a store or a router to be wrong. Prior art is `entryDecision` — the whole
 * entry gate as a pure function, tested without mounting anything.
 */

// **Type-only, and it has to stay so.** A group's tab is the groups feature's word, carried here
// and never read — the pass hands it back to the gate. `groups` imports this feature at runtime,
// so a value import back would close a cycle through both `types.ts` barrels; a type import is
// erased and closes none.
import type { GroupTab } from '@/features/groups/types';
import type { Sport } from '@/shared/vocabulary/sport';

/** A run that produced a Skill rating. **Identifiers only** — see above. */
export interface RatedRun {
  readonly assessmentId: string;
  readonly sport: Sport;
}

/**
 * Where a pass began — which is where it ends. **Every pass begins inside the app now**: the
 * questionnaire left onboarding ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §1, [#730](https://github.com/Rakieta02/Rakieta/issues/730)), and onboarding's own door, *welcome*,
 * went with it.
 *
 * `home` is Home (§7): the picker opened with no group to return to, and a run reached with no
 * pass running — a link, which begins one of its own sport. It ends on Home, which is where the
 * app opens. `passport` is the Skill passport's *Add a sport*: a queue of one, begun at the
 * question route, ending back on the passport.
 *
 * `group` is a group's tab (ADR-0200 §5): an official group's card, *Post a game*'s, Members',
 * or the picker opened from the tab. It ends on that group, **on that tab**, with the chip on
 * the sport just rated — never on the passport, which is where a group's card used to send it.
 * **Identifiers only**, as `rated` is: the group's name is TanStack Query's, read where the
 * way back is labelled, and a copy here would go stale the moment its Owner renamed it.
 *
 * `rankings` is the Rankings page's *Get your {sport} level* ([#775](https://github.com/Rakieta02/Rakieta/issues/775);
 * the rankings mechanics §9): a pass of that one sport, ending back on Rankings **on the sport the
 * page was on** — the one just asked for, rated or not.
 */
export type PassOrigin =
  | { readonly kind: 'home' }
  | { readonly kind: 'passport' }
  | { readonly kind: 'group'; readonly groupId: string; readonly tab: GroupTab }
  | { readonly kind: 'rankings'; readonly sport: Sport };

/**
 * **Where a door into the picker can stand** — a group's tab, or Home. The Skill passport has its
 * own door, *Add a sport*, which never opens the picker, and so has Rankings: its *Get your {sport}
 * level* is one sport, begun at the question route.
 */
export type DoorOrigin = Extract<PassOrigin, { readonly kind: 'home' | 'group' }>;

/** Home — and a run reached with no pass running, which has nowhere else to have begun. */
export const FROM_HOME: Extract<PassOrigin, { readonly kind: 'home' }> = { kind: 'home' };

/** The Skill passport's *Add a sport*. */
export const FROM_THE_PASSPORT: PassOrigin = { kind: 'passport' };

/** Rankings, on the sport the page was on when *Get your {sport} level* was pressed. */
export function fromRankings(sport: Sport): Extract<PassOrigin, { readonly kind: 'rankings' }> {
  return { kind: 'rankings', sport };
}

/** A group's tab — the one the player was on when they pressed the door. */
export function fromAGroup(
  groupId: string,
  tab: GroupTab,
): Extract<PassOrigin, { readonly kind: 'group' }> {
  return { kind: 'group', groupId, tab };
}

export interface OnboardingPass {
  readonly origin: PassOrigin;
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
 * A pass over the sports chosen, with nothing rated yet, begun at one of its doors.
 *
 * A *new* queue is a new pass: whatever an earlier walk produced belongs to that walk, and the
 * way back accounts for this one. The origin is taken rather than defaulted because it is what
 * the ending reads, and a caller that did not say which door it is would be a caller nobody asked.
 *
 * **An empty queue is a pass too**, and a deliberate one: the picker opened from a door and left
 * before anything was chosen. It is begun and over at once, so the gate lands it where it began —
 * the one way back the gate already knows.
 */
export function begin(queue: readonly Sport[], origin: PassOrigin): OnboardingPass {
  return { origin, queue, rated: [] };
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

/**
 * **The sports the picker lists** — every one the server serves, or, where a door narrowed them,
 * only those of them it offers (*+ Another sport*'s, [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §4, [#731](https://github.com/Rakieta02/Rakieta/issues/731)). **The server's order, always**: the
 * offer says which, never in what order, and a sport the server does not serve is not offered
 * whatever a door said.
 */
export function sportsOnOffer(
  served: readonly Sport[],
  offer: readonly Sport[] | undefined,
): readonly Sport[] {
  return offer === undefined ? served : served.filter((sport) => offer.includes(sport));
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
 * **Every door begins a pass, and a link is none of them.** The legitimate ways onto a question
 * are the picker's queue, a card's or a chip's one sport — a pass of exactly one sport, which
 * admits exactly that sport — and the door's *Carry on*, which begins a pass of the run's sport.
 * A link that lands somewhere else — a hand-built URL, a stale notification — is not a shortcut
 * into the middle of a flow, and treating it as one is what produced a questionnaire with no
 * honest progress to show (ADR-0179 §3).
 *
 * The three answers are the three real situations:
 *
 * - **No pass** is a link with nothing running: that run is a genuine pass of one sport,
 *   begun at Home, and it ends there.
 * - **The sport is in the pass** is the ordinary case, every screen after any door.
 * - **A pass is running without this sport** cannot be reached by any flow the app has. The
 *   player goes back to Home, and the door there — or on any group — offers the run again.
 *
 * `start-over` is Home through the entry gate, which no longer resumes anything, so there is no
 * loop to fear: until #730 the gate answered *resume* for an outstanding run, and would have sent
 * this same question back to itself.
 */
export function admissionTo(pass: OnboardingPass | undefined, sport: Sport): PassAdmission {
  if (pass === undefined) return { kind: 'begin' };
  return pass.queue.includes(sport) ? { kind: 'admit' } : { kind: 'start-over' };
}

export type PassDestination =
  /** The next sport the player chose. */
  | { readonly kind: 'rate'; readonly sport: Sport }
  /**
   * Back on Home (ADR-0200 §5) — whatever the pass produced. *Your starting ratings*, the
   * summary that used to stand here, repeated *Your rating* and went with #730.
   */
  | { readonly kind: 'home' }
  /**
   * Back on the Skill passport the pass began from, with the new card drawn — or without
   * it, when the one sport was abandoned (ADR-0179 §3).
   */
  | { readonly kind: 'passport' }
  /**
   * Back on the group the pass began on, on its tab (ADR-0200 §5) — whatever the pass
   * produced, for the passport's reason: she was in the app, and that is the screen she left.
   */
  | { readonly kind: 'group' }
  /** Back on Rankings, on the sport its *Get your {sport} level* was pressed on (#775). */
  | { readonly kind: 'rankings' };

/**
 * Where a player who **stops before the end of the queue** goes.
 *
 * Named on its own because it is asked twice — by a player pressing *done for now* with
 * sports still to go, and by `nextDestination` when there are none left — and one rule
 * answering both is what stops the two from drifting apart.
 *
 * **A pass ends where it began, whatever it produced** (ADR-0200 §5). Every pass begins inside
 * the app now, so rated or abandoned, the player goes back to the screen they left: the group's
 * tab, the passport — which draws the new card itself — or Home. **No pass at all is Home**:
 * nothing began one, and Home is where the app opens.
 */
export function stopDestination(pass: OnboardingPass | undefined): PassDestination {
  if (pass === undefined) return { kind: 'home' };
  switch (pass.origin.kind) {
    case 'passport':
      return { kind: 'passport' };
    case 'group':
      return { kind: 'group' };
    case 'rankings':
      return { kind: 'rankings' };
    case 'home':
      return { kind: 'home' };
  }
}

/**
 * Where the player goes once this sport is dealt with, however it was dealt with.
 *
 * **Finished and abandoned land in the same place**, which is why one rule answers for
 * both. Abandoning is the player saying stop, and it is still the end of that sport: the next
 * sport chosen is still offered, and after the last the player goes back where the pass began
 * (`stopDestination`).
 */
export function nextDestination(pass: OnboardingPass | undefined, sport: Sport): PassDestination {
  if (pass === undefined) return stopDestination(pass);

  const at = pass.queue.indexOf(sport);
  const next = at === -1 ? undefined : pass.queue[at + 1];

  if (next !== undefined) return { kind: 'rate', sport: next };
  return stopDestination(pass);
}

/**
 * What the app lays down for a pass that has just ended, read off where it began.
 *
 * - **home → nothing.** Home is where the app opens, which is where every pass enters it.
 * - **passport → the passport**, the You tab beneath it (ADR-0179 §3).
 * - **rankings → Rankings, on the sport the page was on** (#775) — rated or not: the page reads
 *   the card again, and a level got there turns *No squash level yet* into the list's card.
 * - **group → that group, on the tab it began on, standing on the sport rated last**
 *   (ADR-0200 §3, §5). *The sport just rated* is the last in `rated`: the last sport of the
 *   queue when she finished, the one she stopped after on *Done for now*, the one before an
 *   abandoned sport. **None when nothing was rated** — continue later, the one sport
 *   abandoned, or the picker turned back from — and the page opens on the sport it always would.
 *
 * Asked once, by the gate's app branch, as it ends the pass — so the screens between never
 * read it, and every way out of the pass lands through the same answer.
 */
export type PassReturn =
  | { readonly kind: 'passport' }
  | { readonly kind: 'rankings'; readonly sport: Sport }
  | {
      readonly kind: 'group';
      readonly groupId: string;
      readonly tab: GroupTab;
      readonly sport: Sport | undefined;
    };

export function returnOf(pass: OnboardingPass): PassReturn | undefined {
  switch (pass.origin.kind) {
    case 'home':
      return undefined;
    case 'passport':
      return { kind: 'passport' };
    case 'rankings':
      return { kind: 'rankings', sport: pass.origin.sport };
    case 'group':
      return {
        kind: 'group',
        groupId: pass.origin.groupId,
        tab: pass.origin.tab,
        sport: pass.rated[pass.rated.length - 1]?.sport,
      };
  }
}
