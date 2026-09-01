/**
 * The forecast, the three ways round it comes in, and **the one rule that turns a swap into a
 * selection rather than a request**.
 *
 * ## Every arrangement crosses, so *Even it out* is a choice and not a calculation
 *
 * `ForecastResponse` and `LineupResponse` both carry **all three** pairings of four people,
 * each with its own forecast: *"there are exactly three pairings of four people and the engine
 * walks all three to choose. Returning what it already knows costs nothing and makes* Even it
 * out *a **selection** rather than a calculation — every swap the builder permits is one of
 * these, so there is no arithmetic left for a client to be tempted by."*
 *
 * That is [#228](https://github.com/Raketa02/Raketa/issues/228) §11's answer to §J6's *"the
 * evenness reading, every time a seat changes"*: **only a membership change is a round trip**,
 * and re-arranging is reading a different entry out of a response already held. `searchKeys`
 * says the same thing as a cache key — the forecast is keyed on the **set** of players, so the
 * same four in a different seat order is the same entry.
 *
 * ## Which arrangement is drawn is decided by **your partner**, and by nothing else
 *
 * A court is seated by exchanging two players, and the wire's answer is indexed by pairing.
 * The bridge between them is the one fact a pairing *is*: who is beside you. So a seating
 * selects the arrangement whose `PARTNER` seat holds the player the seating puts in your half,
 * and two seatings that differ only in which opponent stands where select the same one — which
 * is correct, because they are the same game.
 *
 * **`SELF` is how a seat knows it is yours**, and it is `Relationship`'s doing rather than a
 * position's: no route serves a searcher their own player id, so an index would be the only
 * other answer and *seat 0 is you* is a rule the engine states rather than one a client may
 * assume. It also survives the swap that moves you across the net, where the index no longer
 * says anything (`lineup.ts`'s `seatPlaces`).
 *
 * ## No arithmetic happens here, and that is checkable rather than intended
 *
 * `the-play-screens.md` §11.3 — *"no forecast arithmetic: the client selects among arrangements
 * and renders numbers it was given"*, and *"the check for that is looking for arithmetic, not
 * reading intent."* There is one number in this file and it is a seat count.
 */

import type { BuildSeat } from './lineup';
import { seatPlaces } from './lineup';
import type { ForecastAssumption, GroupReason, Relationship, UnfilledReason } from './vocabulary';

/**
 * How even a game is forecast to be — **with its caveat inside it**.
 *
 * `provisional` travels within the forecast rather than beside it, because *"the failure being
 * guarded against is a screen showing the number without its caveat, and a sibling boolean is
 * exactly how the two get separated in a refactor."* This side keeps the shape for the same
 * reason.
 */
export interface Forecast {
  /** Out of a hundred, and drawn as served. Nothing on this side rounds or rescales it. */
  readonly pct: number;
  /** The confidence is part of the claim, so it crosses with it. */
  readonly sigmaGroup: number;
  readonly provisional: boolean;
  /**
   * What the figure assumed.
   *
   * `null` covers two things and deliberately does not tell them apart: **nothing was
   * assumed**, and **the served code is one this build has no words for**. The screen draws
   * §3's gap either way — a caveat it cannot state is not a caveat it may omit — and
   * `provisional` is the field that says whether there was one.
   */
  readonly assumption: ForecastAssumption | null;
}

/** One seat inside one arrangement: where it is, what it is to you, and who is in it. */
export interface ArrangementSeat {
  /** Stable across all three arrangements. The court draws seats in this order. */
  readonly seatIndex: number;
  readonly relationship: Relationship;
  /** **Absent on an open seat.** The line-up's own seat list says why that one is open. */
  readonly playerId?: string;
}

/** One way round, with its own forecast. */
export interface Arrangement {
  readonly pairingId: number;
  /** The one being drawn: the best on a line-up, and the seat order you sent on a forecast. */
  readonly isCurrent: boolean;
  /**
   * Best by the group objective, and **absent on every arrangement when none was computed** —
   * an incomplete four, a singles line-up, and every forecast. Absent is *this does not apply*
   * rather than *this one lost*.
   */
  readonly isBest?: boolean;
  /** The closest game of the three — what *Even it out* selects. */
  readonly isEvenest: boolean;
  /** Both sides, flattened into seat order: A first, you at its head. */
  readonly seats: readonly ArrangementSeat[];
  readonly forecast: Forecast;
}

/**
 * Who is in each seat, as the **builder** holds it — one entry per seat, in seat order.
 *
 * It is the arrangement's own seating until somebody swaps two seats, at which point it is the
 * swapped one and the arrangement is re-selected from it. Nothing here is stored: the
 * membership is `playSession`'s and the arrangements are Query's, and a seating is what you get
 * when you read one through the other.
 */
export type Seating = readonly SeatOccupancy[];

export type SeatOccupancy =
  | { readonly kind: 'you' }
  | { readonly kind: 'player'; readonly playerId: string }
  | { readonly kind: 'empty' };

/**
 * The arrangement a response says is the one to draw — `is_current`, and the first as the
 * fallback.
 *
 * The fallback is not a guess: `is_current` is set by the engine on every answer that has any
 * arrangements at all, so a response arriving without one is a build reading a document it does
 * not know. Drawing the first is then the only thing that is both defined and stable.
 */
export function currentArrangement(arrangements: readonly Arrangement[]): Arrangement | undefined {
  return arrangements.find((one) => one.isCurrent) ?? arrangements[0];
}

/** The closest of the three. What *Even it out* selects, and what it is disabled by. */
export function evenestArrangement(arrangements: readonly Arrangement[]): Arrangement | undefined {
  return arrangements.find((one) => one.isEvenest);
}

/** One arrangement's seating, in seat order — the court's own reading of a pairing. */
export function seatingOf(arrangement: Arrangement): Seating {
  return [...arrangement.seats]
    .sort((one, other) => one.seatIndex - other.seatIndex)
    .map(toOccupancy);
}

function toOccupancy(seat: ArrangementSeat): SeatOccupancy {
  if (seat.relationship === 'SELF') return { kind: 'you' };
  return seat.playerId === undefined
    ? { kind: 'empty' }
    : { kind: 'player', playerId: seat.playerId };
}

/**
 * Trade two seats. **Change sides, never seats** — nobody leaves the court.
 *
 * Total by construction: an index the court could not produce leaves the seating as it was,
 * which is the same answer a swap with itself gives.
 */
export function swapSeats(seating: Seating, from: number, to: number): Seating {
  const one = seating[from];
  const other = seating[to];
  if (one === undefined || other === undefined) return seating;
  return seating.map((held, at) => (at === from ? other : at === to ? one : held));
}

/** The people beside you, **in seat order** — what `ForecastRequest.players` carries. */
export function seatedIds(seating: Seating): readonly string[] {
  return seating.flatMap((seat) => (seat.kind === 'player' ? [seat.playerId] : []));
}

/** How many of the court's seats have somebody in them, yourself included. */
export function seatsFilled(seating: Seating): number {
  return seating.filter((seat) => seat.kind !== 'empty').length;
}

/**
 * Who is beside you — `undefined` on a court with no partner seat at all.
 *
 * Read through `seatPlaces` rather than off an index, because *your* half is the half you are
 * in and a swap can move you across the net. Singles has no `YOUR_PARTNER` place by
 * construction, so the two courts need no branch between them.
 */
export function partnerOf(seating: Seating): SeatOccupancy | undefined {
  const places = seatPlaces(seating.map(toBuildSeat));
  const at = places.indexOf('YOUR_PARTNER');
  return at === -1 ? undefined : seating[at];
}

/**
 * The rules' view of a seat — what `seatPlaces`, `seatLock` and `tapSeat` read.
 *
 * **A hand-seated player has accepted nothing.** Nothing in the builder can seat somebody who
 * has: *opening the builder from an accepted challenge* is out of scope, so `accepted` is
 * `false` at the one place a seating becomes a `BuildSeat` rather than being threaded through
 * the screen — and the truth table keeps its arm for the day a challenge can open one.
 *
 * Exported because the court draws seats through the same narrowing, and two copies of it is
 * two places for that `false` to become something else.
 */
export function toBuildSeat(seat: SeatOccupancy): BuildSeat {
  if (seat.kind === 'you') return { kind: 'you' };
  return seat.kind === 'player' ? { kind: 'player', accepted: false } : { kind: 'empty' };
}

/**
 * **The selection** — which of the three the court is now showing.
 *
 * A pairing is *who is beside you*, so that is what is matched on. Everything else follows:
 * swapping the two opponents selects the same arrangement, because it is the same game and its
 * forecast has not moved; swapping across the net selects another, because it is a different
 * game and the number is supposed to change.
 *
 * The fallback is `is_current` rather than nothing, for the two cases where a partner cannot
 * decide anything: a singles court, which has one way round, and a partner seat that is still
 * empty, where every arrangement of the people actually seated says the same thing.
 */
export function arrangementFor(
  arrangements: readonly Arrangement[],
  seating: Seating,
): Arrangement | undefined {
  const partner = partnerOf(seating);
  if (partner === undefined || partner.kind !== 'player') return currentArrangement(arrangements);

  const matched = arrangements.find((one) => partnerIdOf(one) === partner.playerId);
  return matched ?? currentArrangement(arrangements);
}

/** Who the engine seated beside you in one arrangement. `undefined` while that seat is open. */
function partnerIdOf(arrangement: Arrangement): string | undefined {
  return arrangement.seats.find((seat) => seat.relationship === 'PARTNER')?.playerId;
}

/**
 * **The seating to draw when nobody has moved anybody** — the whole of what a builder's court
 * is, before a swap.
 *
 * The current arrangement's, where there is one; and before there is, *you, and the people you
 * have added, in the order you added them*. The second half is what a court looks like while a
 * forecast is in flight and on a court nobody has been seated on at all, and it is the reason
 * a screen holding this needs no separate empty state.
 *
 * **Seat 0 is yours** because the engine's own roster puts it there — *"there is no
 * arrangement in which the searcher crosses the net"* — and the swap that moves you produces a
 * seating this function is never asked for, because by then there is an arrangement to read.
 */
export function seatingToDraw(
  arrangements: readonly Arrangement[],
  court: { readonly seats: number; readonly members: readonly string[] },
): Seating {
  const local = localSeating(court.seats, court.members);
  const drawn = arrangementFor(arrangements, local);
  return drawn === undefined ? local : seatingOf(drawn);
}

/** You at seat 0, then whoever has been added, then holes. Not exported: it is the fallback. */
function localSeating(seats: number, members: readonly string[]): Seating {
  return Array.from({ length: seats }, (_, at) => {
    if (at === 0) return { kind: 'you' } as const;
    const member = members[at - 1];
    return member === undefined
      ? ({ kind: 'empty' } as const)
      : ({ kind: 'player', playerId: member } as const);
  });
}

/**
 * The seat a *pick somebody* control opens against — **the first hole**.
 *
 * A full court answers seat 0, which is the only index that is always a seat: the control is
 * not drawn there, and an index a court could not produce is not a state to write a branch for.
 */
export function firstEmptySeat(seating: Seating): number {
  const at = seating.findIndex((seat) => seat.kind === 'empty');
  return at === -1 ? 0 : at;
}

/**
 * Who an add against this seat would **replace** — and nobody, on every other kind of seat.
 *
 * The pool is opened against a seat, and whether that makes the next add an addition or a
 * replacement is a fact about the seat rather than a rendering. `undefined` covers all three
 * ways there is nobody to replace: no seat was named, the index is one this court could not
 * produce, and the seat is empty or the searcher's own.
 *
 * Total by construction, like `swapSeats` and `firstEmptySeat` beside it: a seating has exactly
 * as many entries as the court has seats, so an index outside it is not a state to write a
 * branch for.
 */
export function seatOccupant(seating: Seating, at: number | undefined): string | undefined {
  const seat = at === undefined ? undefined : seating[at];
  return seat?.kind === 'player' ? seat.playerId : undefined;
}

/**
 * One seat of the court a **line-up answer** returned, with the reason it is open.
 *
 * The shortfall rides here and not on an arrangement, because *why could this not be filled* is
 * a fact about the pool and the mask rather than about a way round: all three arrangements of
 * one answer are short of the same people.
 */
export interface SeatedSeat {
  readonly seatIndex: number;
  readonly relationship: Relationship;
  readonly playerId?: string;
  /**
   * §11's per-seat obstacle, or `null` on a seat that is taken.
   *
   * `null` also covers a code this build has no words for. That is a **drop** rather than a
   * gap: an empty seat with nothing to say is the state a forecast's own open seats are
   * already in — the searcher simply has not filled them — and no total on the screen counts
   * shortfall statements.
   */
  readonly unfilled: UnfilledReason | null;
}

/**
 * The court a `POST /lineups` seated: seat by seat, every way round, and the two things the
 * answer as a whole has to say.
 *
 * **A partial line-up is this shape with fewer people in it** — never a different one, and
 * never an error — so the builder renders one thing whether the engine seated nobody, three of
 * four, or all of them.
 */
export interface SeatedCourt {
  readonly seats: readonly SeatedSeat[];
  readonly arrangements: readonly Arrangement[];
  /** Why this four beat the runner-up. `null` where there was no runner-up to beat. */
  readonly groupReason: GroupReason | null;
  /**
   * `NO_SHARED_SLOTS` when the four of you have no hour in common — **a dock, never a
   * refusal**. Nobody is removed from the court for it, and the honest line is that you would
   * all have to bend.
   */
  readonly dock: UnfilledReason | null;
}

/**
 * The seated court as a **seating** — the same reading `seatingOf` gives an arrangement.
 *
 * `LineupSchema.seats` is *"the court as it currently stands, seat by seat, in the arrangement
 * marked `is_current`"*, so the two agree by construction; this is the one that also knows
 * which seats are open and why, and it is what the line-up's membership is read off after a
 * fill.
 */
export function courtSeating(court: SeatedCourt): Seating {
  return [...court.seats]
    .sort((one, other) => one.seatIndex - other.seatIndex)
    .map((seat) =>
      seat.relationship === 'SELF'
        ? ({ kind: 'you' } as const)
        : seat.playerId === undefined
          ? ({ kind: 'empty' } as const)
          : ({ kind: 'player', playerId: seat.playerId } as const),
    );
}

/**
 * The shortfall by seat index — what the court draws under each empty seat.
 *
 * Keyed by index rather than carried on the seating, because an empty seat cannot be swapped:
 * `tapSeat` answers `OPEN_POOL` for one in **both** modes, so a hole never moves and an index
 * is a stable name for it.
 */
export function shortfallBySeat(court: SeatedCourt): ReadonlyMap<number, UnfilledReason> {
  return new Map(
    court.seats.flatMap((seat) =>
      seat.unfilled === null ? [] : [[seat.seatIndex, seat.unfilled]],
    ),
  );
}
