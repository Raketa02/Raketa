/**
 * **A game still filling, in detail** — `GET /proposals/{id}` (#542), the details a card's **i**,
 * a *You're In* row and a live yes open ([#557](https://github.com/Raketa02/Raketa/issues/557); the
 * screens A4.2; the mechanics §14.2).
 *
 * Pure. The read is the server's whole answer — who is In, the sides and their forecast, the club
 * and its distance, the share and the book-by, the overlap, the status and **what the reader may do
 * now** (`actions`) — and nothing it decides is re-derived. What is decided here is only what a yes
 * said on the details does to the court, which the deck's card carries and the details' read does
 * not: the deck's own rule, *your yes leaves the seats open less one* (`open_seats_after_your_yes`
 * is `open_seats − 1` on the server), read off the seats and the In count the details carry.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import { youAreIn, type DeckCard, type Overlap } from './deck';
import type { YesOn, YourPayment } from './fill';
import { deadlineAhead, paymentWindowAt, type Deadline, type YourTime } from './home';
import type { CardType, CourtState, GameKind, ProposalStatus, ReaderAction } from './vocabulary';

/** One game still filling, as its details read it. */
export interface ProposalDetails {
  readonly proposalId: string;
  /** The group the game is dealt in — its pool is filed under the group's id. */
  readonly groupId: string;
  readonly type: CardType;
  readonly kind: GameKind;
  readonly sport: Sport;
  /** Who a challenge names; absent on a pick and once its poster withdrew. */
  readonly challenger?: DeckCard['challenger'];
  /** The instant the status and the actions were folded against. */
  readonly readAt: string;
  readonly status: ProposalStatus;
  /** What the reader may do now, in the screen's order — empty once the game is over. */
  readonly actions: readonly ReaderAction[];
  /**
   * The refused payment to confirm — present exactly when `actions` holds `CONFIRM_PAYMENT` — with
   * their time to pay while it runs.
   */
  readonly yourPayment?: YourPayment;
  /** People In on the whole game. */
  readonly inCount: number;
  /** Four in padel and badminton, two otherwise. */
  readonly seats: number;
  readonly startsAt: string;
  /** The club and how far it is — never a court, which is given at booking. */
  readonly where: DeckCard['club'] & { readonly distanceKm?: number };
  readonly shareGrosze: number;
  /** The book-by: when the game leaves unfilled. */
  readonly deadline: string;
  readonly noFreeCancellation: boolean;
  /**
   * **When the payment the game waits for is due** (#625, #626) — one player's share was refused and
   * their seat is theirs alone until then: *Waiting for one payment · until 14:40*. Never whose; the
   * reader's own is `yourPayment.confirmBy`. Present on `WAITING_FOR_A_PAYMENT` alone, and absent
   * from an older server.
   */
  readonly paymentDueBy?: string;
  /**
   * Everybody drawn, the reader on their own side: their card as the deck deals it while they decide;
   * everybody In once they are In — the open seats drawn empty.
   */
  readonly sides: DeckCard['sides'];
  readonly forecast?: DeckCard['forecast'];
  readonly overlap: Overlap;
}

/**
 * **What a yes from the details does to the court** — *Book it now* when it is the last seat,
 * a free vote otherwise; nothing to book for a reader whose yes is already said.
 */
export function courtOfDetails(
  details: Pick<ProposalDetails, 'seats' | 'inCount' | 'sides'>,
): CourtState {
  return completesTheGame(details) ? 'BOOK_IT_NOW' : 'COURT_AVAILABLE';
}

/** *You complete it* — your yes would leave no seat open, and you have not given it yet. */
export function completesTheGame(
  details: Pick<ProposalDetails, 'seats' | 'inCount' | 'sides'>,
): boolean {
  return details.seats - details.inCount === 1 && !youAreIn(details);
}

/** **What the fill holds for a yes said on the details** — `useFillYes`'s card. */
export function yesOnDetails(details: ProposalDetails): YesOn {
  return {
    proposalId: details.proposalId,
    type: details.type,
    court: courtOfDetails(details),
    sides: details.sides,
  };
}

/**
 * **A time to pay, as the money row names it** (#625, #626; Q111) — the payment the game waits for
 * (*until 14:40*), and the reader's own (*Confirm your payment by 14:40*, or before the cut-off *Fix
 * your card by 14:40*, #638; Q113), each only while it is ahead of `now`.
 */
export interface PaymentDue {
  readonly dueBy?: Deadline;
  readonly yours?: YourTime;
}

export function paymentDueOf(
  details: Pick<ProposalDetails, 'paymentDueBy' | 'yourPayment'>,
  now: number,
): PaymentDue {
  const dueBy = deadlineAhead(details.paymentDueBy, now);
  const payment = details.yourPayment;
  const by = deadlineAhead(payment?.confirmBy, now);
  const paymentWindow = paymentWindowAt(payment?.confirmBy, payment?.timeTo, now);
  return {
    ...(dueBy === undefined ? {} : { dueBy }),
    ...(by === undefined ? {} : { yours: { by, window: paymentWindow } }),
  };
}

/**
 * **Whether the money row names a deadline that leaves by itself** — a time to pay (*until*), or the
 * reader's own: the details' clock ticks while one is there, as Home's does (`lineCanRunOut`).
 */
export function detailsCanRunOut(
  details: Pick<ProposalDetails, 'paymentDueBy' | 'yourPayment'>,
): boolean {
  return details.paymentDueBy !== undefined || details.yourPayment?.confirmBy !== undefined;
}
