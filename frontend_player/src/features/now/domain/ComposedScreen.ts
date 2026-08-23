/**
 * The composed screen, in this app's own vocabulary.
 *
 * `ADR-0070` serves Now as **three ordered regions and one fact about the
 * viewer**, and this is that shape mapped inward. Three things about it are
 * decisions rather than transcription:
 *
 * - **A region is present and empty, never absent.** The wire already promises
 *   that; keeping it here means a player with nothing gets a shape she
 *   recognises, and the *not there* / *there and empty* pair — the most
 *   productive bug in this class — never gets two code paths.
 * - **A card carries its situation's *copy*, not its code.** Resolving a code to
 *   a sentence is what `mappers/` is for, and it is the layer allowed to read
 *   `@/generated`; a component that received the code would have to hold the
 *   table, and `domain/` may not name the generated union at all. `status` is
 *   `undefined` for a name this build has never heard of — the card still draws,
 *   and loses exactly the thing that is actually missing (`ADR-0070`).
 * - **Nothing here is derived.** `ADR-0053` leaves the phone one derivation —
 *   subtracting a moment it was handed from the current time — and that lives in
 *   `countdown.ts`. Every field below arrived on the wire.
 *
 * The spine is deliberately narrower than the contract: the fit badge, the
 * emphasis flag, `mayDepart` and the act code are the match card's
 * (`Raketa02/Raketa#87`) and the shelves' (`#88`), and a field mapped here with
 * no reader would be `ADR-0071`'s refusal wearing a domain object's clothes.
 */

import type { Money } from '@/shared/lib/formatting';

import type { SituationCopy } from './presentation';

/** Indoor or outdoor — a fact about *where*, on the spine of every card. */
export type Cover = 'indoor' | 'outdoor';

/**
 * An instant, exactly as the server wrote it.
 *
 * Held as the string it arrived as rather than as a `Date`, so that nothing in
 * the feature can be tempted to read a component off it. It is subtracted from
 * the current time and otherwise passed along.
 */
export type Moment = string;

/** Where: the club, the clock face its matches start on, a roof, and how far. */
export interface Place {
  readonly clubId: string;
  readonly clubName: string;
  /**
   * The club's IANA zone. A match at 19:00 reads `19:00` to a player sitting in
   * London, so this never comes from the device (`ADR-0070`).
   */
  readonly zone: string;
  readonly cover: Cover;
  readonly distanceKm: number | undefined;
}

/** A match, as one card. */
export interface MatchCard {
  readonly kind: 'match';
  readonly matchId: string;
  /**
   * The one moment this card is about, sometimes absent. The client's whole rule
   * is *if there is a moment here, count to it* — it is **not** the moment the
   * card next changes.
   */
  readonly clock: Moment | undefined;
  /** A live seat claim's five minutes, when this viewer holds one (`ADR-0081`). */
  readonly claimExpiresAt: Moment | undefined;
  readonly where: Place;
  readonly price: Money;
  /**
   * The situation's name as it arrived.
   *
   * Kept as a string and never branched on: it is here so an unknown name can be
   * reported and so `status` being absent has a cause a reader can see.
   */
  readonly situation: string;
  /** What the situation says, or absent for a name this build has never heard. */
  readonly status: SituationCopy | undefined;
}

/** A player who has just arrived. No situation, no clock, no price. */
export interface PersonCard {
  readonly kind: 'person';
  readonly playerId: string;
  readonly nickname: string;
}

/** A club that has just joined. No situation, no clock, no price. */
export interface ClubCard {
  readonly kind: 'club';
  readonly clubId: string;
  readonly name: string;
  readonly distanceKm: number | undefined;
}

/**
 * Three card types, not one with holes (`ADR-0070`).
 *
 * A single union with optional halves would give every person card an
 * always-empty situation, an always-empty clock and an always-empty price, with
 * nothing preventing a later session filling one in.
 */
export type NowCard = MatchCard | PersonCard | ClubCard;

/** Seats offered to this viewer, soonest-to-expire first. */
export interface OffersRegion {
  readonly cards: readonly MatchCard[];
}

/** The matches this viewer is committed to, chronological. */
export interface EnrolledRegion {
  readonly cards: readonly MatchCard[];
}

/**
 * One shelf: what it claims, an optional caption, and its cards.
 *
 * `title` and `caption` are resolved here rather than carried on the wire —
 * `ADR-0070` keeps shelf presence and shelf order on the server and leaves the
 * words with the client. Either is `undefined` for a code this build has never
 * heard of, which is the same answer as *draw nothing for it*.
 */
export interface Shelf {
  readonly code: string;
  readonly title: string | undefined;
  readonly caption: string | undefined;
  readonly cards: readonly NowCard[];
}

/** The shelves, in the server's order. A shelf with nothing in it is absent. */
export interface ShelvesRegion {
  readonly shelves: readonly Shelf[];
}

/**
 * What is owed, and the one consequence of owing it.
 *
 * `blocked` is the server's boolean and the client never derives it from the
 * amount: concluding *she owes, therefore create is dead* would be a rule, and
 * the phone holds none.
 */
export interface DebtLine {
  readonly owed: Money;
  readonly blocked: boolean;
}

/** The whole screen: three regions, and the one fact about the viewer. */
export interface ComposedScreen {
  readonly offers: OffersRegion;
  readonly yourMatches: EnrolledRegion;
  readonly shelves: ShelvesRegion;
  readonly debt: DebtLine | undefined;
}
