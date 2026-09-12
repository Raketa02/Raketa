/**
 * **The five rungs a game's card is named by, read in order** — and the single most drift-prone
 * thing on the map
 * ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.3).
 *
 * ```
 * 1. a seat is open                          → Needs a player
 * 2. the agreed point exists and has passed  → Needs result
 * 3. the agreed day is today                 → Today
 * 4. all three slots filled                  → Game on
 * 5. otherwise                               → Planning
 * ```
 *
 * **Read in order, and the clock outranks the checklist**
 * ([ADR-0145](../../../../../docs/adr/0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md)
 * §3). The conditions overlap on purpose — a game arranged for tonight has three slots filled
 * *and* is today *and* will shortly have a point behind it — so the order is what resolves them,
 * and rungs 4 and 5 are reached only when the point has not passed and the day is not today.
 * #329's *"and the agreed moment still ahead"* is implied by the ladder rather than restated as a
 * condition of its own.
 *
 * **And the open seat outranks the clock** (#411 rule 5,
 * [ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)).
 * A seat somebody left is a fact about the **court** and not about the plan: the game cannot be
 * played, and the server refuses to record it, until somebody is in that seat — so *Needs result*
 * over a short court would ask for a score nobody could enter, and *Today* would announce a game
 * that has a gap in it. The plan survives underneath (rule 6); it is the rung that changes.
 * Nothing on the wire names it: the standing stays `AWAITING_ENTRY` and the seat is
 * `player_id: null`, and this is the one place the two are read together.
 *
 * **It is here because five card names, two tickets and one amendment all key on it.**
 * [#324](https://github.com/Raketa02/Raketa/issues/324) and
 * [#329](https://github.com/Raketa02/Raketa/issues/329) each keyed a rule on the agreed point
 * without the two ever being checked against each other, and #324's second amendment dropped
 * *Today*'s three-slot requirement — so this is one function, in `domain/`, and every surface
 * reads it: the rail, the card, the gloss, and the game screen's arm.
 *
 * ## It folds against the games list's instant and against nothing else
 *
 * Every instant arrives as an argument and the one that arrives is `GET /games`' `read_at`
 * ([ADR-0148](../../../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
 * §10). `GET /plans` deliberately carries no `read_at` — a plan folds nothing against the clock —
 * so **Now has one clock by construction** rather than by a rule anybody remembers, and there is
 * no `Date.now()` here for a standing printed beside a rung to disagree with. The seats arrive
 * with it, off the same list, so the court a rung is read on is the court that instant describes.
 *
 * ## `import type`, and the arrow it keeps
 *
 * The court is `features/games`' shape, read here as a **type** — `gameCard.ts`'s own line, for
 * the same reason: `features/plans` may import `features/games` and never the reverse (ADR-0149
 * §1), and a type crossing leaves nothing of that feature in this module at runtime.
 */

import type { Game } from '@/features/games/types';
import { platformDay } from '@/shared/date/platformZone';

import { unfilledSlots, type Plan } from './slots';

/**
 * **The five rungs, in the order they are read**, and the type derived from them rather than
 * declared beside them — `SPORTS` → `Sport`'s own shape, so the list and the union cannot
 * disagree about what a rung is.
 */
export const RUNGS = ['needs-a-player', 'needs-result', 'today', 'game-on', 'planning'] as const;

/** A card's name is one of these or an ending's. */
export type Rung = (typeof RUNGS)[number];

/**
 * Whether a card name is one of the five — **the ladder's own membership test.**
 *
 * Exported because the gloss is *one rule for four rungs*, and a hand-written cascade over the
 * rungs is the shape that goes quietly wrong when another arrives: it would fall through to the
 * sentence written for an ended game.
 */
export function isRung(name: string): name is Rung {
  return (RUNGS as readonly string[]).includes(name);
}

/**
 * **The moment this plan names** — the value the ladder's first rung is about.
 *
 * > The agreed instant when the day and the hour are both recorded; the **start of the following
 * > local day** when only the day is; **nothing** when no day is.
 *
 * **Later rather than earlier, so nobody is asked for a result before they could have played** —
 * a game with a day and no hour is not asked at breakfast about an evening that has not happened.
 *
 * It is **derived by the server and never recomputed here**: it is a zone conversion, the app
 * refuses zone-aware formatters for the reason `shared/date/platformZone.ts` records, and a
 * second implementation would be a second answer to *when is this game* on one screen. So this
 * function is where the definition lives and the value is the plan's own — which is what makes
 * *the agreed point is `domain/` beside the ladder* true without spelling the arithmetic twice.
 */
export function agreedPoint(plan: Plan | undefined): string | undefined {
  return plan?.agreedPoint;
}

/**
 * **The court a rung is read on** — the seats, and the instant the games list was folded at.
 * A `Game` is one; the two fields are all the ladder reads of it.
 */
export type CourtRead = Pick<Game, 'readAt' | 'seats'>;

/**
 * Which rung this plan is on, for this court, against the instant the games list was folded at.
 *
 * A plan of `undefined` is a game nobody has arranged anything on — `GET /plans` has no row for
 * one — and it is *Planning*, which is the same answer an empty plan gets, because the two are
 * one state.
 *
 * **A seat with nobody in it is read first**, before the clock: `playerId` absent is the wire's
 * `player_id: null`, a seat somebody left and nobody has filled (ADR-0162). The rule is spelled
 * here rather than imported, on the same line the file's `import type` keeps — it is one field,
 * and `features/games`' `openSeats` reads the same one.
 *
 * **An instant this build cannot read has not passed.** A rung is a claim about the clock, and
 * the safe direction is the one that goes on asking somebody to arrange a game rather than the
 * one that asks them for the result of a game that may still be ahead of them.
 */
export function rungOf(plan: Plan | undefined, court: CourtRead): Rung {
  if (court.seats.some((seat) => seat.playerId === undefined)) return 'needs-a-player';
  if (momentHasPassed(plan, court.readAt)) return 'needs-result';
  if (plan?.day !== undefined && plan.day === platformDay(court.readAt)) return 'today';
  if (unfilledSlots(plan).length === 0) return 'game-on';

  return 'planning';
}

/**
 * **Whether the agreed moment is behind the fold** — the first clock rung's own test, exported.
 *
 * It is what draws *Leave this game* only while the moment is ahead (#411 rule 1): the server
 * refuses a departure past the agreed moment with `game_moment_has_passed`, and the client
 * mirrors that rule off the same instant rather than offering a control the act would refuse.
 * *Needs a player* outranks *Needs result*, so the rung alone cannot say it — a short court past
 * its moment is still *Needs a player*, and this is the fact the rung folds over.
 *
 * Unreadable on either side answers *no*, and so does a plan with no agreed point: the safe
 * direction is the one that keeps the act available on a game that may still be ahead.
 */
export function momentHasPassed(plan: Plan | undefined, readAt: string): boolean {
  const point = agreedPoint(plan);
  if (point === undefined) return false;

  const at = Date.parse(point);
  const read = Date.parse(readAt);

  return !Number.isNaN(at) && !Number.isNaN(read) && at <= read;
}
