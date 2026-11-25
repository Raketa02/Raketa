/**
 * **A group's Fill in and You’re in tabs** — the rescues the reader is offered, on Fill in, and their
 * own yeses on games still filling, on You’re in ([#557](https://github.com/Raketa02/Raketa/issues/557),
 * a tab each since #847; the screens A3; the mechanics §10).
 *
 * Pure. Which rescues the reader fits and is free for, in what order and until when, is the
 * server's (`GET /pools/{id}/fill-in`, #545); which yeses are live is the live yeses' (#539). What
 * is decided here is only what the tab draws of them at an instant: a row leaves at its deadline
 * — at the cut-off a game short of a seat is off, at the start it is under way — whether or not the
 * server has swept it yet, as a card at its deadline leaves the deck.
 */

import type { ReadStage } from '@/shared/lib/query-client';
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

/**
 * The tab's read, for one sport. **The wire's `badge` is not read** (#849): the tab's badge is
 * worked out from the rows still standing, minus the ones seen (`seen.ts`); the field stays on the
 * wire for older installed apps (ADR-0208, *Harder*).
 */
export interface FillIn {
  /** The instant every row and deadline was read against, on the server's clock. */
  readonly readAt: string;
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
 * **The ids Fill in counts** (ADR-0208 §1, #849) — the booking of each rescue row still standing,
 * which is what its badge counts and what the tab marks seen.
 */
export function rescueIds(standing: readonly Pick<SeatToFill, 'bookingId'>[]): readonly string[] {
  return standing.map((row) => row.bookingId);
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
 * ***You’re in*** (§10.2) — the reader's live yeses in this group and sport, in the list's order:
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
 * **The ids You’re in counts** (ADR-0208 §1, #849) — the proposal of each live yes in this group and
 * sport (`yesesIn`): what its badge counts and what the tab marks seen.
 */
export function yesIds(here: readonly Pick<LiveYes, 'proposalId'>[]): readonly string[] {
  return here.map((yes) => yes.proposalId);
}

/**
 * **What You’re in draws with no yes of the reader's** (#847; the screens A3; split Q3) — the group's
 * starting card only once Fill in has said there is nothing too, since the card tells you to post
 * and both lists are empty; one line, *You haven’t said yes to a game here yet*, while Fill in has a
 * rescue or could not say; and nothing yet — the spinner — while Fill in's read is on its way, so the
 * starting card is never a first frame. `rescues` are the ones standing, `undefined` until read.
 */
export type YoureInEmpty = 'startingCard' | 'line' | 'waiting';

export function youreInEmpty(
  rescues: readonly SeatToFill[] | undefined,
  rescuesHeld: boolean,
): YoureInEmpty {
  if (rescues === undefined) return rescuesHeld ? 'line' : 'waiting';
  return rescues.length === 0 ? 'startingCard' : 'line';
}

/**
 * **How far You’re in's first read has come** ([#875](https://github.com/Raketa02/Raketa/issues/875))
 * — what the group page's reveal waits on for the tab: the reader's live yeses, and **with no yes
 * here, Fill in's read too**, since the starting card waits for it (`youreInEmpty`). `here` is how
 * many yeses the read holds in this group and sport, `undefined` until it has landed.
 */
export function youreInRead(
  yeses: ReadStage,
  here: number | undefined,
  rescues: ReadStage,
): ReadStage {
  if (yeses !== 'landed') return yeses;
  return here !== undefined && here > 0 ? 'landed' : rescues;
}

/**
 * **A You’re in row's squares** — everybody In on the game, the reader among them, then a dashed
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
 * **Whether a You’re in row offers *Withdraw*** — only once its game's details say the reader may:
 * while the full game waits for one payment they say *Leave* instead (A3.2, #625), and a withdrawal
 * then would leave the game with no sheet in front of it. Nothing before the details are read.
 */
export function mayWithdraw(details: Pick<ProposalDetails, 'actions'> | undefined): boolean {
  return details?.actions.includes('WITHDRAW') ?? false;
}
