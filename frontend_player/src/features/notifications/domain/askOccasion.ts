/**
 * When the explainer is worth showing, and the one rule that decides it.
 *
 * `ADR-0061` gives the ask exactly two occasions and no third: **during
 * onboarding**, where *Turn on* / *Not now* is explained before anything fires,
 * and again **at the first standby join**, which is the moment the interruption
 * has a reason. It amends `ADR-0052`'s *in context, not at launch* on the ground
 * that most recipients of an offer never join a standby list, so an ask that
 * only fired there would leave most of the ladder unreachable.
 *
 * **The two occasions are not symmetrical, and only one of them is a decision.**
 * Onboarding is a step in a linear flow reached once, by a player who has just
 * installed the app: the screen is where it is, and the OS prompt is spent only
 * on a yes, so there is nothing to decide. A standby join is an act she may take
 * fifty times, and showing the explainer on the fiftieth would be nagging — so
 * that occasion is the one with a rule, and it is here.
 */

import type { NotificationStanding } from '@/shared/lib/notifications';

/**
 * Whether spending the OS prompt can still buy anything.
 *
 * The question is never *what did she answer* — it is *may we still ask*. iOS
 * grants exactly one system dialog per install and two denials on Android are
 * permanent, so a build that has already spent the prompt has nothing to gain
 * from explaining anything, and a build she has already said yes to has nothing
 * left to explain.
 */
export function promptIsAvailable(standing: NotificationStanding): boolean {
  return standing === 'askable';
}

export interface StandbyJoinAsk {
  readonly standing: NotificationStanding;
  /**
   * Whether a standby join has already carried the explainer.
   *
   * **This app session, and not for ever**, which is a deliberate narrowing of
   * `ADR-0061`'s *"the first standby join"*: nothing on this phone persists a
   * decision except the OS keychain, which holds credentials and nothing else,
   * and `AsyncStorage` is banned outright. The nearest precedent is onboarding's
   * own deferred runs, which last one session for the same reason.
   *
   * The residual is bounded and one-sided: the only player who meets the
   * explainer twice is one who tapped *Not now* and then joined a queue in two
   * different sessions, and she meets it at a moment she has just asked to be
   * told when a seat frees.
   */
  readonly askedThisSession: boolean;
}

/**
 * Whether this standby join should carry the explainer.
 *
 * **The first join, not every join.** The second thing joining a queue buys her
 * is the interruption (`ADR-0062`), so the ask belongs to the act — but an ask
 * repeated on every act is furniture, which `ADR-0066` refuses by name for the
 * declaration and which is no less true here.
 */
export function explainAtStandbyJoin({ standing, askedThisSession }: StandbyJoinAsk): boolean {
  return promptIsAvailable(standing) && !askedThisSession;
}
