/**
 * A line-up, the **origin search** it belongs to, and the one guard over the three acts that
 * would orphan it.
 *
 * ## A line-up belongs to a search, not to a screen
 *
 * `POST /forecasts` takes `search_id` as an **Origin key** and refuses players who did not
 * appear in that search — *"every player named must have appeared in"* it. So a line-up
 * cannot be four player ids: it is **`{ originSearchId, seats }`**, and three separate spec
 * requirements stop being policy a build session has to remember and become arithmetic
 * ([#228](https://github.com/Raketa02/Raketa/issues/228) §1):
 *
 * | Requirement | How the origin key answers it |
 * | --- | --- |
 * | **AC-70** — an abandoned search must not later alter the line-up you are looking at | The abandoned run minted a different id. Nothing reads it. |
 * | **H-23 / AC-8** — changing sport discards the line-up | A search is per sport, so the origin is gone. |
 * | **G7** — acting from a screen that has gone out of date | There is now a name for *what* went stale. |
 *
 * The seats are **ids and nothing else**. Every fact drawn about a seated player — the name,
 * the level, the photograph, the reasons — is read back off that search's own rows, held in
 * Query under `searchKeys.detail(originSearchId)`. Part 1's *"never copy Query data into
 * Zustand"* is not a rule being obeyed here; it is the reason AC-70 needs no guard.
 *
 * The wire agrees about the order: `ForecastRequest.players` is *"the people beside you, **in
 * seat order**: the first is your partner"*, one, two or three, and **a seat may be empty** —
 * which is why an unfilled seat is the absence of an entry rather than a hole in the list.
 * Where each id ends up sitting is the arrangement's business, and arrangements come back
 * from the server.
 *
 * ## Invalidity is derived, and the two stores never sync
 *
 * A line-up's **origin** is `(sport, mode, the week that was asked)` — the three things
 * `SearchEnvelope` and `POST /lineups` carry between them, `availability_override` being the
 * third. It is not sport alone, which is the only trigger AC-8 covers.
 *
 * So `playSession` holds the line-up, `playPreferences` holds sport and mode, and **nothing
 * writes across them**. A line-up is orphaned when the origin it was built under is no longer
 * the origin the player is now searching under, which is read at the moment somebody asks —
 * never synchronised at the moment something changes. That is what makes two stores safe here
 * where `profileDraft`'s docblock warns against splitting: *"two stores would mean two things
 * to reset and a sync that can be forgotten"*, and there is no sync to forget.
 *
 * ## Three triggers, one guard
 *
 * Left alone the derivation discards a line-up **silently** — the builder simply opens empty —
 * which is §G6 bug #6's own complaint (*"silently destroys an in-progress line-up, with no
 * confirmation"*) reappearing under two triggers no acceptance criterion covers. The builder is
 * pushed from Find a game and back pops to it, so a player really can build four seats, go
 * back, and change the mode or edit the week.
 *
 * **The confirmation attaches to the act that mutates any part of the origin**, not to sport.
 * `changingTheOrigin` below is that one guard, and it is deliberately not exported;
 * `changingSport`, `changingMode` and `leavingFindAGame` are its three callers and hold one
 * line each — which field of the origin moves. A fourth origin field added later
 * inherits the guard for free, and sport stops being a special case — the same shape
 * [#261](https://github.com/Raketa02/Raketa/issues/261) found for the reset, *two criteria,
 * one function*.
 *
 * **The week is the exception that proves it.** A modal on every grid tap would be
 * intolerable, so its trigger is *leaving Find a game with a changed origin* rather than each
 * tap — which is the moment the *Keep these times?* prompt already occupies, and therefore not
 * a new interruption.
 *
 * ## What this file is still owed
 *
 * [`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md) §7
 * assigns `lineup.ts` five things. Two are here — origin validity and the three triggers behind
 * one guard — because they are the state model. The other three are **the court's**, and they
 * arrive with the screen that draws it: **side derivation under H-25** (squash puts both
 * players on the same half, so seat 3 is not where seat 3 is in padel), **locked seats**, and
 * **§B7's swap truth table**. They are named here rather than left to be rediscovered: a seat's
 * side is meaningless without a court, and a swap is a re-arrangement of a response the builder
 * already holds.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { SearchMode } from './vocabulary';
import { sameWeek, type WorkingWeek } from './workingWeek';

/**
 * What a search was run for — the three facts a line-up's validity is judged against.
 *
 * The week is in here because `POST /lineups` carries it as `availability_override`: a
 * shortlist composed against Tuesday evenings is not a shortlist against Saturday mornings,
 * and a line-up built from the first is not a line-up in the second.
 */
export interface PlayOrigin {
  readonly sport: Sport;
  readonly mode: SearchMode;
  readonly week: WorkingWeek;
}

/**
 * A search this client ran, by id, with what it was asked for.
 *
 * **The envelope alone cannot answer this.** `SearchEnvelope` carries `search_id` and `mode`
 * and neither the sport nor the week — those were the *request's*, so the origin is folded
 * onto the record in `api/` when the mutation's response is written into
 * `searchKeys.detail(id)`. That is what a DTO is for, and it is why *origin search* is a name
 * this app owns rather than a wire type.
 */
export interface OriginSearch {
  readonly searchId: string;
  readonly origin: PlayOrigin;
}

/**
 * A player id in a seat. The name and the level are the search's, read back by this id.
 *
 * The alias earns its place where a field name would not: `seats` is otherwise
 * `readonly string[]`, and *which* strings is the load-bearing claim this whole model rests
 * on. `originSearchId` and `OriginSearch.searchId` stay bare `string` deliberately — they say
 * what they hold in their own names, and a second alias that is not a distinct type would buy
 * documentation nothing was missing.
 */
export type SeatedPlayerId = string;

/**
 * The four (or two) you are composing, and the search they came off.
 *
 * `seats` holds only the people **beside** you and only the ones actually added, so a
 * half-built line-up is this shape with fewer entries — never a different one, and never a
 * list with holes in it.
 */
export interface Lineup {
  readonly originSearchId: string;
  readonly seats: readonly SeatedPlayerId[];
}

/** Whether two searches were run for the same thing. The week compares as a set. */
export function sameOrigin(one: PlayOrigin, other: PlayOrigin): boolean {
  return one.sport === other.sport && one.mode === other.mode && sameWeek(one.week, other.week);
}

/**
 * Everything any rule below needs: the line-up, the search it came off, and what the player is
 * searching for **now**.
 *
 * One type because the three never travel apart — every question about a line-up is a question
 * about the distance between two origins, and a rule that took them loose would let a caller
 * pass a line-up beside somebody else's origin search. Each is read from its own owner at the
 * call site: the line-up from `playSession`, the origin search from
 * `searchKeys.detail(lineup.originSearchId)`, and *now* from `playPreferences` and the working
 * copy. **Assembling them to ask a question is not synchronising them** — nothing is written
 * back, which is what lets the two stores stay two stores.
 */
export interface LineupInPlay {
  readonly lineup: Lineup | undefined;
  /** Whatever Query holds for `lineup.originSearchId`. Undefined is a real, handled state. */
  readonly originSearch: OriginSearch | undefined;
  readonly now: PlayOrigin;
}

/**
 * Where a line-up stands against what the player is searching for **now**.
 *
 * `unreadable` is not a failure: it is the honest answer while the origin search has not been
 * read back yet, or when the cache no longer holds it. A screen that cannot say whether a
 * line-up is current must not act as though it is, and must not throw it away either — the
 * server re-checks at send, which is where an origin nobody can produce is settled.
 */
export type LineupStanding =
  | { readonly kind: 'none' }
  | { readonly kind: 'current' }
  | { readonly kind: 'orphaned' }
  | { readonly kind: 'unreadable' };

/**
 * Read the standing off the origin — the derivation the whole model rests on.
 *
 * `originSearch` is whatever `searchKeys.detail(lineup.originSearchId)` holds. Nothing is
 * passed in that a store keeps in step with another store.
 */ export function lineupStanding({ lineup, originSearch, now }: LineupInPlay): LineupStanding {
  if (lineup === undefined || lineup.seats.length === 0) return { kind: 'none' };
  if (originSearch === undefined || originSearch.searchId !== lineup.originSearchId) {
    return { kind: 'unreadable' };
  }
  return sameOrigin(originSearch.origin, now) ? { kind: 'current' } : { kind: 'orphaned' };
}

/**
 * What one of the three triggers costs, as a decision the screen carries out.
 *
 * `seated` is on the ask because the sentence names it — a confirmation that cannot say how
 * many people it is about is a confirmation nobody can weigh. It is read off the line-up
 * itself, so it can be said even when the origin search cannot be read.
 */
export type OriginChange =
  { readonly kind: 'go' } | { readonly kind: 'ask'; readonly seated: number };

/**
 * **The guard**, and the only one. The three exported triggers below differ from one another
 * in a single line each: which field of the origin they move.
 *
 * It goes ahead on every act that changes nothing — re-selecting the sport already selected
 * raises no modal, which is what keeps a confirmation worth reading.
 *
 * **It asks when the origin search cannot be read.** The tempting alternative is to go ahead,
 * on the grounds that a line-up whose origin is already unreadable was not lost *by this act*.
 * That is the reasoning §G6 bug #6 is a complaint about: the outcome either way is a line-up
 * destroyed *"silently, with no confirmation"*, and which of two causes destroyed it is not
 * something the player can see. The seat count is known either way, so the sentence can still
 * be written; asking costs one modal in a state `RANKED_LIST_QUERY_OPTIONS` makes very rare,
 * and going ahead costs the whole of what the guard is for.
 */
function changingTheOrigin(inPlay: LineupInPlay, next: PlayOrigin): OriginChange {
  const standing = lineupStanding({ ...inPlay, now: next });
  if (standing.kind === 'none' || standing.kind === 'current') return { kind: 'go' };
  return { kind: 'ask', seated: inPlay.lineup?.seats.length ?? 0 };
}

/** Trigger one: the sport chips. AC-8's *"discarded entirely"*, and the only one it names. */
export function changingSport(inPlay: LineupInPlay, sport: Sport): OriginChange {
  return changingTheOrigin(inPlay, { ...inPlay.now, sport });
}

/** Trigger two: the mode segment. `SearchEnvelope` carries `mode`, so it is part of the origin. */
export function changingMode(inPlay: LineupInPlay, mode: SearchMode): OriginChange {
  return changingTheOrigin(inPlay, { ...inPlay.now, mode });
}

/**
 * Trigger three: **leaving Find a game** with a week the search was not run on.
 *
 * Not each tap on the grid — see the docblock. It passes `now` through unchanged, and that is
 * the point rather than an omission: the other two ask *what if this field moved*, and this one
 * asks about a field that has **already** moved, because the working copy is edited in place.
 * Comparing it against the origin's week is what makes a cell ticked and unticked not an edit.
 */
export function leavingFindAGame(inPlay: LineupInPlay): OriginChange {
  return changingTheOrigin(inPlay, inPlay.now);
}
