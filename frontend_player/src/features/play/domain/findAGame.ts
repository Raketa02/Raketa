/**
 * What stands between a player and a search — the three rules the *Find a game* screen reads.
 *
 * Each of them is a question a screen would otherwise answer inline, and two of them are
 * questions the **server** answers with a refusal if the screen gets them wrong:
 * `sport_not_rated` and `play_intent_not_declared`. Both refusals are documented as backstops
 * rather than as the designed path
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §2), so
 * what is here is how the screen avoids reaching them.
 *
 * ## `sport_not_rated` is settled by construction
 *
 * *"The sport chips are drawn only for rated sports."* So the chip row is a projection of
 * `GET /ratings` and there is no reachable state in which a player selects a sport the search
 * would refuse — the `409` survives for a stale profile on a second device and is never
 * something this screen produces.
 *
 * ## `play_intent_not_declared` is a screen the client opens **knowingly**
 *
 * ADR-0094 makes the search screen the edit surface and gates *"a searcher with a rating but
 * no declaration"* behind **a one-tap interstitial** — *"permanent, not a migration path: it
 * is what makes the coverage rule true rather than merely intended."* The join it needs is
 * free: the profile read carries only the sports that were **declared** in, so *rated ∧ absent
 * from the map* is a set difference over two lists the screen already holds, which is exactly
 * what [ADR-0021](../../../../../docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md)
 * licenses a client to compute. `sports_needing_declaration` was refused on the wire for that
 * reason.
 *
 * **The interstitial is not the mode toggle**, and the two must not be collapsed. The toggle
 * is a `SearchMode` with two values, process-scoped and never written back; the interstitial
 * writes a `PlayIntent` with three. That arity gap is ADR-0094's central move and
 * `domain/playMode` is where the whole of it is argued — a screen that let the toggle stand in
 * for the declaration would be re-seeding the toggle from the declaration on every open, which
 * is the exact case the drift backstop is written for and would leave it nothing to catch.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { PlayIntent } from './vocabulary';

/** Whatever the profile read carries, as the screen holds it: absence means *undeclared*. */
export type Declarations = Readonly<Partial<Record<Sport, PlayIntent>>>;

/**
 * Where the screen stands, in the only three states it has.
 *
 * `no-rated-sport` is unreachable from the flow — the Play tab is behind a rating — and is
 * represented anyway for the reason the entry gate represents its own unreachable branches:
 * the alternative is a screen that renders a chip row of nothing and a search control that
 * would refuse, with no sentence to say why.
 */
export type FindAGameStanding =
  | { readonly kind: 'searchable'; readonly sport: Sport }
  /** Rated in this sport and never asked what kind of game — the interstitial's state. */
  | { readonly kind: 'undeclared'; readonly sport: Sport }
  | { readonly kind: 'no-rated-sport' };

/**
 * The sport the screen is on: the one the player chose, or the first they are rated in.
 *
 * The fallback is not a default so much as a **repair**. `playPreferences` is process-scoped
 * and outlives any single read, so a sport chosen last week can survive a rating being
 * withdrawn or a build that no longer names it — and a chip row where nothing is selected is
 * a screen whose search control has no sport to send.
 *
 * **Order is the server's.** `GET /ratings` answers in sport-registry order and nothing here
 * sorts, so *the first rated sport* is the same sport at both ends.
 */
export function sportOnScreen(
  rated: readonly Sport[],
  chosen: Sport | undefined,
): Sport | undefined {
  if (chosen !== undefined && rated.includes(chosen)) return chosen;
  return rated[0];
}

/** The three rules, read together — see the module note for why they are one function. */
export function findAGameStanding(
  rated: readonly Sport[],
  chosen: Sport | undefined,
  declarations: Declarations,
): FindAGameStanding {
  const sport = sportOnScreen(rated, chosen);
  if (sport === undefined) return { kind: 'no-rated-sport' };
  return declarations[sport] === undefined
    ? { kind: 'undeclared', sport }
    : { kind: 'searchable', sport };
}
