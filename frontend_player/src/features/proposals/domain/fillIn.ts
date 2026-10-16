/**
 * **A group's Fill in tab** — *Seats to fill*, the rescues the reader is offered, and *You're In*,
 * their own yeses on games still filling ([#557](https://github.com/Raketa02/Raketa/issues/557);
 * the screens A3; the mechanics §10).
 *
 * Pure. Which rescues the reader fits and is free for, in what order and until when, is the
 * server's (`GET /pools/{id}/fill-in`, #545); which yeses are live is the live yeses' (#539). What
 * is decided here is only what the tab draws of them at an instant: a row leaves at its deadline
 * — at the cut-off a game short of a seat is off, at the start it is under way — whether or not the
 * server has swept it yet, as a card at its deadline leaves the deck.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import { peopleOn, type DeckCard, type DeckPerson } from './deck';
import type { ProposalDetails } from './details';
import { yesOnRescue, type YesOn } from './fill';
import type { RescueOffer } from './home';
import type { LiveYes } from './liveYes';
import type { GameKind } from './vocabulary';

/**
 * **One *Seats to fill* row** — a booked game that lost a player, offered to the reader (A3.1): the
 * same offer its details carry seen from outside (`RescueOffer` — how long, and whether it fills by
 * the cut-off), and the game.
 */
export interface SeatToFill extends RescueOffer {
  /** The booking — *I'm in* takes its seat, and its details are read from outside. */
  readonly bookingId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
  readonly startsAt: string;
  readonly club: DeckCard['club'];
  /** What the club calls the court. */
  readonly courtName: string;
  /** What *I'm in* charges at once. */
  readonly shareGrosze: number;
  /** The dashed **?** squares after the players' posters. */
  readonly openSeats: number;
  /** Everybody on the game, each *paid* — the small posters, first side first. */
  readonly players: readonly DeckPerson[];
}

/** The tab's read, for one sport. */
export interface FillIn {
  /** The instant every row and deadline was read against, on the server's clock. */
  readonly readAt: string;
  /** The tab's badge: the *Seats to fill* rows. */
  readonly badge: number;
  /** Soonest first. */
  readonly seatsToFill: readonly SeatToFill[];
}

/** **The rows still offered at `now`** — a row whose deadline has passed leaves silently. */
export function standingSeats(rows: readonly SeatToFill[], now: number): readonly SeatToFill[] {
  return rows.filter((row) => {
    const deadline = Date.parse(row.deadline);
    return Number.isNaN(deadline) || deadline > now;
  });
}

/**
 * **What the fill holds for a row's *I'm in*** — the booking's seat. A row holds no sides: it lists the
 * players, not which side the seat is on, so *It's a game!* reads them off the booking once the seat
 * is taken.
 */
export function yesOnRow(row: Pick<SeatToFill, 'bookingId'>): YesOn {
  return yesOnRescue(row);
}

/**
 * ***You're In*** (§10.2) — the reader's live yeses in this group and sport, in the list's order:
 * picks, challenges and posts, never a rescue, which goes straight to Home.
 */
export function yesesIn(
  yeses: readonly LiveYes[],
  groupId: string,
  sport: Sport,
): readonly LiveYes[] {
  return yeses.filter((yes) => yes.groupId === groupId && yes.sport === sport);
}

/**
 * **A You're In row's squares** — everybody In on the game, the reader among them, then a dashed
 * square per seat still open: the game's own details, read for the row.
 */
export function squaresOfYes(details: Pick<ProposalDetails, 'sides' | 'seats' | 'inCount'>): {
  readonly people: readonly DeckPerson[];
  readonly open: number;
} {
  return {
    people: peopleOn(details).filter((person) => person.isIn),
    open: Math.max(0, details.seats - details.inCount),
  };
}

/**
 * **Whether a You're In row offers *Withdraw*** — only once its game's details say the reader may:
 * while the full game waits for one payment they say *Leave* instead (A3.2, #625), and a withdrawal
 * then would leave the game with no sheet in front of it. Nothing before the details are read.
 */
export function mayWithdraw(details: Pick<ProposalDetails, 'actions'> | undefined): boolean {
  return details?.actions.includes('WITHDRAW') ?? false;
}
