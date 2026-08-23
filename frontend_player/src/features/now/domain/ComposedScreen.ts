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
 * The spine is deliberately narrower than the contract: a field mapped here with
 * no reader would be `ADR-0071`'s refusal wearing a domain object's clothes. `act`
 * and `mayDepart` arrived with the action row (`#87`) and the fit badge with the
 * shelves (`#88`), each with the thing that draws it. What is still absent is the
 * fit's `target` — the Level a match is aimed at, which crosses only when it is
 * precise and which no card draws today.
 */

import type { Money } from '@/shared/lib/formatting';

import type { FitBadge } from './fitBadge';
import type { ActCopy, DoorCopy, SituationCopy } from './presentation';

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
  /**
   * What her own departure took, for a viewer who has left — absent for everyone
   * else, which is every card until she leaves one.
   *
   * **Beside the situation and never instead of it.** An audience changes a
   * card's words and which money it names, and never the situation (`ADR-0072`):
   * a leaver keeps the match's own progress, because whether her money comes
   * back depends entirely on the seat refilling and a card that hid the match's
   * progress would hide the only thing that decides her outcome.
   *
   * Resolved to a sentence here for the same reason `status` is — the wire sends
   * a form and a payload, and turning either into words is `mappers/`' job.
   */
  readonly departure: string | undefined;
  /**
   * The one act this card names, already resolved to its label and its
   * destination — or absent, which twenty-six of the thirty-six situations are.
   *
   * **In the spine, and never derived from the situation** (`ADR-0083`). That is
   * what lets a phone meeting an unknown name still take the seat, and it is why
   * a card whose status line is missing can still carry a button. `undefined`
   * covers both *no act* and *an act this build cannot resolve*, because a button
   * whose destination is unknown is the one outcome worse than silence.
   */
  readonly act: ActCopy | undefined;
  /**
   * Whether this viewer may leave, as the server's boolean (`ADR-0086`).
   *
   * A spine fact rather than an act code: leaving is not the card's act, and one
   * card may not carry two. The phone is forbidden from concluding *I hold a seat*
   * (`ADR-0053`), so either the server says or the control cannot be drawn at all.
   */
  readonly mayDepart: boolean;
  /**
   * Why this match is suggested, or absent.
   *
   * Absent on every card the viewer is already in — a badge answers *why this one*,
   * and that question is not asked about a match she has paid for — and on a screen
   * the server could not score, which arrives with no badges rather than with
   * invented ones. It is **not** absent because she holds no rating at the sport:
   * `ADR-0084` answers that viewer with a door where the ranked shelves would be, so
   * no card of hers reaches this field at all.
   */
  readonly fit: FitBadge | undefined;
  /**
   * Whether this is the one card on the screen that shouts (`ADR-0037`).
   *
   * **The server's flag, and never a comparison.** Emphasis is fit ≥ 90 *and*
   * coverage ≥ 80 % *and* a seat open, capped at one card per screen and silenced
   * entirely by an offer — every clause of which is about the *other* cards, so it
   * is a property of the composed screen (`ADR-0032`) rather than of this one. The
   * phone cannot see coverage at all and must not learn to guess at it.
   */
  readonly emphasis: boolean;
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
  readonly kind: 'shelf';
  readonly code: string;
  readonly title: string | undefined;
  readonly caption: string | undefined;
  readonly cards: readonly NowCard[];
}

/**
 * The way into a sport's questionnaire, where that sport's shelves would be.
 *
 * `ADR-0084`: a player who taps a chip for a sport she holds no rating at is owed
 * a destination, and it arrives **in the list, in order** — never as a flag, and
 * never as something the phone concludes from shelves that are missing. That
 * inference would fire wrongly on any day the city genuinely has nothing in a
 * sport she *is* rated at, and `ADR-0053` leaves the phone no rules to draw one
 * with. So a door exists here exactly when one arrived on the wire.
 *
 * `copy` is `undefined` for a code this build has never heard of, which is the
 * same answer as *draw nothing for it* — a door whose sentence is blank and
 * whose button says nothing is worse than the missing row.
 */
export interface Door {
  readonly kind: 'door';
  readonly code: string;
  readonly copy: DoorCopy | undefined;
}

/**
 * What the shelves list may hold.
 *
 * Heterogeneous by design rather than by accident: the door takes the ranked
 * shelves' **position**, so *New on Raketa* and *New clubs* still compose beneath
 * it — the clubs are the argument for spending the two minutes. A union is what
 * makes a renderer that fails to narrow a type error rather than a blank row.
 */
export type Block = Shelf | Door;

/**
 * The blocks, in the server's order. A shelf with nothing in it is absent.
 *
 * Named `blocks` where the wire names it `shelves`. The wire keeps its name
 * because renaming a field breaks every shipped client reading a region that has
 * not otherwise changed; nothing outside this app reads *this* type, so the list
 * is called what it holds.
 */
export interface ShelvesRegion {
  readonly blocks: readonly Block[];
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

/**
 * What Now needs to correct itself off the player's own tap (`ADR-0070`).
 *
 * **One card and nothing else, today.** Every action off Now hands its own
 * answer *and* this back in one response (`ADR-0074`), so returning from a route
 * the server has just finished computing costs no second ask — which matters
 * here more than anywhere, because popping back off a route is deliberately none
 * of `ADR-0054`'s four occasions and Now would otherwise still be showing the
 * card as it was before the act.
 *
 * A departure returns the card **changed, in place** — same match, same region,
 * new rendering — so neither viewer-owned region's contents or order moves and
 * there is nothing for a region slot to hold. The wire grows one when the first
 * action that moves a region lands, which is taking a seat
 * (`Raketa02/Raketa#89`). **The shelves are never in an update at all**, which is
 * what stops a match moving under her thumb (`ADR-0032`).
 */
export interface NowUpdate {
  readonly card: MatchCard;
}

/** The whole screen: three regions, and the one fact about the viewer. */
export interface ComposedScreen {
  readonly offers: OffersRegion;
  readonly yourMatches: EnrolledRegion;
  readonly shelves: ShelvesRegion;
  readonly debt: DebtLine | undefined;
}
