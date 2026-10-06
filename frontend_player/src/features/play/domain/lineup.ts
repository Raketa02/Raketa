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
 * ## A seat can go out of date, and it is marked rather than emptied
 *
 * The other thing that can happen to a line-up while nobody is looking: a seated player the
 * live gates have since stopped admitting. That is `withheldSeats` below, and it is the same
 * discipline as the origin — a **set difference**, derived at the moment somebody asks, never
 * stored and never synchronised.
 *
 * ## And the three the court brought with it
 *
 * [`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md) §7
 * assigns `lineup.ts` five things. Two are the state model above; the other three arrived with
 * the component that draws a court and are in the second half of this file — **side derivation
 * under H-25**, **locked seats** and **§B7's swap truth table**.
 *
 * They are rules and not drawings, which is the whole of why they are here: a side somebody
 * could be wrong about (squash puts both players on the same half of the picture), a seat
 * somebody could wrongly empty, and a tap whose meaning depends on what is already held. What each
 * of them *says* is `components/courtPresentation.ts`', and what any of it *looks like* is
 * `components/court/`'s — §7's line, drawn once.
 */

import type { SeatPlace } from '@/shared/vocabulary/seatPlace';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Candidate, SearchEnvelope } from './candidate';
import type { SeatedCourt } from './forecast';
import type { SearchMode } from './vocabulary';
import { sameWeek, type WorkingWeek } from './workingWeek';

/**
 * What a search was run for — the facts a line-up's validity is judged against.
 *
 * The week is in here because `POST /lineups` carries it as `availability_override`: a
 * shortlist composed against Tuesday evenings is not a shortlist against Saturday mornings,
 * and a line-up built from the first is not a line-up in the second.
 */
export interface PlayOrigin {
  readonly sport: Sport;
  readonly mode: SearchMode;
  /**
   * The week the search ran on — **absent where none was composed**, which is the legal value
   * meaning *against the grid the profile holds*.
   *
   * Every search started on *Find a game* has one, because that screen is where a week is
   * improvised. A fill that completes a challenge has none: there was no *Find a game* to
   * improvise on, so the ask omits `availability_override` and the answer is the profile's own
   * grid ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md) §7).
   * It is **absent rather than empty** because an empty week is a real, different value — *I
   * unticked every cell* — and #247 is what stopped the wire conflating the two.
   */
  readonly week?: WorkingWeek;
  /**
   * The half-built court this search exists to **finish** — absent on every search composed on
   * *Find a game*.
   *
   * It is part of the origin rather than a flag on a screen because it is *what the search was
   * run for*, in exactly the sense the other fields are: ADR-0150 §2 reads the sport, the mode
   * and the locked seats off the challenge and **refuses all three beside it**, so the challenge
   * is not one more thing sent alongside an ask — it *is* the ask. Everything downstream reads
   * it off the record and nothing is passed a second time (`the-loop-components.md` §4.2: *no
   * `from` parameter*).
   */
  readonly completing?: CompletingChallenge;
}

/**
 * A challenge being completed, and **who on it has already said yes.**
 *
 * The two travel together because the second is only ever read about the first. `accepted` is
 * derived once, from the detail the challenge screen is already holding at the moment ⚡ is
 * pressed — a set the fill's own answer cannot state, because the people who accepted *"come
 * back as ordinary candidate rows"* and an ordinary row says nothing about a challenge.
 *
 * It is what makes `BuildSeat.accepted` true for the first time: an accepted seat is not a
 * control — no clear badge, no press, no pool — and swapping is the only thing that works on
 * it, which **draws** *an acceptance is to the game, not to the side* rather than writing it
 * (ADR-0150 §8).
 */
export interface CompletingChallenge {
  readonly challengeId: string;
  /** Player ids that answered `ACCEPTED`. Never the whole court: an empty seat has said nothing. */
  readonly accepted: readonly SeatedPlayerId[];
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
 * **What `searchKeys.detail(id)` actually holds** — the origin, and the answer under it.
 *
 * [#228](https://github.com/Raketa02/Raketa/issues/228) §1: *"every ranked list in Play is a
 * mutation-minted record held under `searchKeys.detail(id)`"*, and §7 gives that entry the
 * whole of `RANKED_LIST_QUERY_OPTIONS`. Until the builder there was no surface drawing a
 * seated player, so the entry held only the origin and the docblock above said the rows
 * *"join it when a surface draws one"*. The builder is that surface: every fact about
 * somebody in a seat — the name, the level, the photograph — is read back off these rows by
 * id, which is the whole reason `Lineup.seats` may be ids and nothing else.
 *
 * `court` is present on a **line-up answer** and absent everywhere else, which is the honest
 * shape: `POST /searches` ranks people and seats nobody, and only `POST /lineups` has a court
 * with a shortfall to state.
 */
export interface SearchRecord extends OriginSearch {
  readonly envelope: SearchEnvelope;
  /** Ranked, and withheld rows already dropped — see `withheldSeats` for what that costs. */
  readonly candidates: readonly Candidate[];
  /** Only `POST /lineups` seats a court. */
  readonly court?: SeatedCourt;
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

/**
 * Whether the sport puts four people on the court, or two — **the one branch behind every
 * sentence and every rule in this feature that could otherwise have said *four* out loud.**
 *
 * The count itself is `courtSeatCount`'s: `Court`'s own coordinates, counted rather than
 * listed, so a fifth sport arrives with a drawing and not with an entry anywhere. What is here
 * is the **boundary** over it, and there is exactly one of it — a second `seats > 2` written
 * one screen away is a squash court told to build a four.
 *
 * **It is in `domain/` because it is a rule and not copy**
 * ([`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md)
 * §7). It lived in `builderPresentation` while every reader was a sentence; it moved when
 * `atStake` needed it ([#312](https://github.com/Raketa02/Raketa/issues/312)) and a `domain/`
 * file reaching into the copy deck would have been the wrong direction for the same
 * dependency. The copy modules import it from here and read the same way.
 */
export const isDoubles = (seats: number) => seats > 2;

/**
 * Whether two searches were run for the same thing. The week compares as a **set**.
 *
 * **A composed week is never the same origin as an uncomposed one**, and that is the reading
 * the optional field could otherwise get wrong: *absent* is *the profile's grid, whatever it
 * says today*, and `[]` is *every cell unticked* — two answers that a `?? []` would collapse
 * into one, silently, in the function the whole orphan model rests on.
 */
export function sameOrigin(one: PlayOrigin, other: PlayOrigin): boolean {
  if (one.sport !== other.sport || one.mode !== other.mode) return false;
  // Two fills of two different courts are two origins, whatever else they agree about.
  if (one.completing?.challengeId !== other.completing?.challengeId) return false;
  if (one.week === undefined || other.week === undefined) return one.week === other.week;
  return sameWeek(one.week, other.week);
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

/**
 * The seats whose players the **live gates no longer admit**, as a set difference.
 *
 * ## Why a difference, and not a tombstone
 *
 * `WithheldRowSchema` has exactly **one field**. There is nowhere on it for a reason, an id, a
 * card or a breakdown to be written, because
 * [ADR-0130](../../../../../docs/adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)'s rule is that the other side
 * sees no trace in any response — and that rule does not weaken because the surface has a
 * longer memory. So a withheld row cannot say *who*.
 *
 * It does not need to. The line-up's seats hold the players themselves and the read-back's
 * live rows carry `player_id`, so a seated player who is no longer among the live rows **is**
 * the mark. No positional arithmetic, no cache archaeology.
 *
 * ## Derived, never stored
 *
 * The same discipline as the origin: *invalidity is derived from the origin* rather than
 * synchronised, which is why the two stores need no sync. A stored mark is a third thing that
 * can be stale about staleness, and it would outlive the read-back that justified it — the
 * exact shape of the cached hold flag §J6 forbids by name.
 *
 * It follows that **a mark appears only after a pool visit**, because that is when the
 * read-back happens, and navigation is never gated on a request. `undefined` live rows is that
 * state and marks nobody: with no read-back held, reading *no live rows* as *everybody is
 * gone* would mark a whole court on a cold cache.
 *
 * ## What the mark may say, and what it may not
 *
 * **The seat is marked, not emptied.** Emptying is the silent destruction the origin guard
 * exists to prevent, arriving from a direction no acceptance criterion covers; doing nothing
 * lets the player build on somebody who is gone and find out at the last possible moment.
 * Marking states the fact where they can act on it, one tap from the pool, and leaves the send
 * as the backstop rather than the discovery.
 *
 * **A marked player stays seated, and stays in the forecast.** Dropping them would make the
 * number silently disagree with the court in front of the player, and would force a *second*
 * cause for `provisional` — which was deliberately collapsed to exactly one.
 *
 * **The court states the fact and never the cause**: four gates reach this mark wearing one
 * sentence, exactly as they reach the withheld row. That sentence is
 * [`courtPresentation.ts`](../components/courtPresentation.ts)'s.
 *
 * @param liveIds the `player_id`s the origin search's read-back still holds, or `undefined`
 *   when no read-back is held at all.
 */
export function withheldSeats(
  lineup: Lineup | undefined,
  liveIds: readonly SeatedPlayerId[] | undefined,
): readonly SeatedPlayerId[] {
  if (lineup === undefined || liveIds === undefined) return [];
  const live = new Set(liveIds);
  return lineup.seats.filter((seated) => !live.has(seated));
}

/**
 * Who stays on the court when the line-up **moves onto another search's list** — the people
 * that list returned, in the order they were seated, and nobody else.
 *
 * ## Why a line-up ever moves
 *
 * ⚡ mints a search of its own and the line-up rebinds to it, because `POST /forecasts` refuses
 * anybody the cited search never showed. But that record **returns exactly the people it
 * seated** — a court is its answer, not a list — so a pool opened on it would offer the one
 * person just taken off and nobody else. The list a player picks from is the ranked one the
 * court was searched under, and a pick off it has to bind the line-up to *that* search, or the
 * next forecast is refused.
 *
 * ## Why the difference, and not everybody
 *
 * The same bound, read from the other end: the new origin can vouch only for the rows it
 * returned. A seat it never showed cannot travel — the forecast and the send would both refuse
 * the four — so it leaves the court, and the pool **says so before the tap** rather than
 * letting the court empty itself afterwards. That is `the-play-screens.md` §5.1's own sentence
 * about re-running: the other seats are only *probably* in the new answer, and a line-up that
 * moves is honestly a new line-up.
 *
 * Membership only. Where the arrangement is read from is the origin's business, and a seat that
 * stays keeps its place in seat order.
 *
 * @param seats the line-up's seats, less anybody the pick is replacing.
 * @param returnedIds the `player_id`s the list being picked from returned.
 */
export function carriedOnto(
  seats: readonly SeatedPlayerId[],
  returnedIds: readonly SeatedPlayerId[],
): readonly SeatedPlayerId[] {
  const returned = new Set(returnedIds);
  return seats.filter((seated) => returned.has(seated));
}

// ---------------------------------------------------------------------------
// The court: H-25's sides, the locked seats, and the swap truth table
// ---------------------------------------------------------------------------

/**
 * One seat of a court being built, as **the rules** see it.
 *
 * Three facts and no more: whether it is yours, whether somebody is in it, and whether that
 * somebody has already accepted. The name, the level, the photograph and the per-seat
 * shortfall are the seat's to draw and none of them changes what a tap does — a component's
 * own seat type is a superset of this one and passes straight in.
 */
export type BuildSeat =
  | { readonly kind: 'you' }
  | {
      readonly kind: 'player';
      /**
       * They have already said yes to a challenge this builder is completing.
       *
       * *"The people who already said yes are fixed — they can change sides, never seats."*
       * It is a fact about the seat rather than about the person: the same player is freely
       * replaceable in a line-up nobody has sent.
       */
      readonly accepted: boolean;
    }
  | { readonly kind: 'empty' };

/**
 * The two **halves** of a court, as everything that speaks about one of them names it.
 *
 * `SeatPlace` is three values because a listener placing a seat needs the role as well as the
 * side; a half is two, because a court has two of them. The fold is not a formatting detail —
 * *your partner is on your half* is exactly the kind of thing somebody can be wrong about, and
 * it is the reason a predicate over one place would be the wrong shape here.
 */
export type CourtHalf = 'yours' | 'theirs';

/**
 * Which half a place is on — **read off the place, never off the index or the drawing.**
 *
 * `seatPlaces` has already done the hard half of this: it is what knows squash seats both
 * players on the same half of the picture (H-25), and that a side **follows you** across the
 * net when swap mode moves you. This is the fold from its three values onto the two a caller
 * asking *is this seat on the half I want* can compare against.
 *
 * **Total, and that is the whole argument for the shape.** It was
 * `mine !== (place !== 'THEIR_SIDE')` inside `handlesOn`, which is two inversions to hold in
 * your head and, worse, a rule keyed on one value: a fourth `SeatPlace` would join *your* half
 * silently, by falling through the negation, and nothing would fail. A function over the
 * vocabulary answers every member explicitly ([#300](https://github.com/Raketa02/Raketa/issues/300)).
 */
export function courtHalfOf(place: SeatPlace): CourtHalf {
  switch (place) {
    case 'YOUR_SIDE':
    case 'YOUR_PARTNER':
      return 'yours';
    case 'THEIR_SIDE':
      return 'theirs';
  }
}

/**
 * **The lock** — a seat nobody may vacate: **yours, and anybody who has already accepted.**
 *
 * Two reasons and one rule rather than a special case beside a rule. Your own seat is not
 * something the builder is composing — it is the thing everything else is composed around —
 * and an acceptance is a promise the product has already made on somebody else's behalf.
 *
 * **It answers *whether*, and no longer *why*.** It returned a `SeatGuard` code — one per
 * reason — for exactly as long as a tap on a locked seat was refused out loud, and the
 * refusal had to name which reason it was. Removing the swap toggle removed both refusals
 * with it: a tap trades now, and trading across the net is the one thing a locked seat was
 * always allowed to do. What is left is a single question with a single reader, and a code
 * nothing prints is a vocabulary with no listener.
 */
export function seatIsLocked(seat: BuildSeat): boolean {
  return seat.kind === 'you' || (seat.kind === 'player' && seat.accepted);
}

/**
 * Whether a seat may be emptied — and therefore **whether its clear badge is drawn at all**.
 *
 * That is why there are two guard toasts and not four. The prototype drew the badge on every
 * occupied seat and then refused two of them with a message; a refusal nobody can trigger is
 * a message nobody has to read.
 */
export function seatIsClearable(seat: BuildSeat): boolean {
  return seat.kind === 'player' && !seatIsLocked(seat);
}

/**
 * What a tap on a seat **means** — never what it writes.
 *
 * Every arm is a decision the screen carries out: the pool is a navigation, the swap is a
 * re-arrangement of a response the builder already holds, and the refusal is a toast. Nothing
 * here touches a line-up, which is what lets the whole truth table be read in one place.
 */
export type SeatTap =
  /** Fill this seat. One act: the pool is opened against a seat with nobody in it. */
  | { readonly kind: 'OPEN_POOL'; readonly seat: number }
  | { readonly kind: 'SELECT'; readonly seat: number }
  | { readonly kind: 'DESELECT' }
  | { readonly kind: 'SWAP'; readonly from: number; readonly to: number };

/**
 * **The swap truth table**, and the whole of what a seat does when it is pressed.
 *
 * ```
 * empty            open the pool against this seat
 * nothing held     select
 * this seat        deselect
 * another seat     trade the two
 * ```
 *
 * ## Swapping is not a mode, and losing the mode is what made it four rows
 *
 * The table had seven rows and a toggle over them, because a tap on an occupied seat meant
 * two different things and a switch beside the court was what told them apart: *replace this
 * player* with the toggle off, *trade these two* with it on. The toggle is gone
 * (`BuilderScreen`), and with it the only reason a seat's tap had a mode at all — **a seat
 * trades, always**, and the court says so in one sentence above it.
 *
 * **An empty seat is still tested first, and it is the only row that is not a trade.** There
 * is nothing in it to swap, and tapping a hole means the obvious thing.
 *
 * **Replacing somebody is now the clear badge and then the hole it leaves.** That is a real
 * cost — two taps where there was one — and it is the trade the toggle's removal makes: the
 * × is drawn on exactly the seats a replacement was ever allowed against
 * (`seatIsClearable`), so nothing that could be replaced has stopped being replaceable, and
 * *Pick players myself* still opens the pool on the first empty seat.
 *
 * **Both refusals went with the mode.** They belonged to the replacement and never to the
 * trade — *change sides, never seats* — so your own seat and an accepted one were always
 * freely movable across the net, and it was only being replaced that they refused. With no
 * replacement on a tap there is nothing left to refuse, which is why `seatIsLocked` no longer
 * says which reason it is and `courtPresentation` no longer writes either sentence.
 *
 * The seat is passed rather than looked up, so this is total: a court draws its own seats, and
 * an index it could not produce is not a state to write a branch for.
 *
 * @param selected the seat already held for a trade, or `undefined` when none is.
 */
export function tapSeat(selected: number | undefined, index: number, seat: BuildSeat): SeatTap {
  if (seat.kind === 'empty') return { kind: 'OPEN_POOL', seat: index };
  if (selected === undefined) return { kind: 'SELECT', seat: index };
  if (selected === index) return { kind: 'DESELECT' };
  return { kind: 'SWAP', from: selected, to: index };
}
