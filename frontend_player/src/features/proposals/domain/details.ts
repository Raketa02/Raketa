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
  /**
   * A **competitive** game's full forecast — the deck's figure with the two side strengths it was
   * read from (#833). Never sent on For fun, nor where somebody on it holds no level in the sport.
   */
  readonly forecast?: DetailsForecast;
  /** What a counted result would do to **your** Level — the pair, or absent (see {@link AtStake}). */
  readonly atStake?: AtStake;
  readonly overlap: Overlap;
}

/**
 * **How even the game drawn is forecast, and the two side strengths it was read from** — the
 * figures a booked game's pairing prints as its forecast and its split, for the same people standing
 * the same way (ADR-0207 §6). One computation: while a seat is empty the % is `provisional`, and so
 * are the strengths.
 */
export interface DetailsForecast {
  readonly pct: number;
  readonly provisional: boolean;
  readonly split: {
    readonly yourSide: number;
    readonly theirSide: number;
    /** `yourSide − theirSide`, **signed and served** — never subtracted here. */
    readonly gap: number;
  };
}

/**
 * **What a counted result on this game would do to your Level** — *If you win +0,08 · If you lose
 * −0,07*, priced as a booked game's pairing prices it. Two values or none: absent while a seat is
 * open, once the game is no longer yours to play, once it is booked, and where there is nothing to
 * price.
 */
export interface AtStake {
  readonly winDelta: number;
  readonly lossDelta: number;
}

/**
 * **The card the details open on, above the game card** — the kind's own: a competitive game's
 * full forecast with what is at stake (#839; for fun 3). For fun's Social vibe card is #840's.
 */
export type DetailsTopCard = {
  readonly kind: 'forecast';
  readonly forecast: DetailsForecast;
  readonly atStake?: AtStake;
};

/**
 * **The kind's own card, or nothing.** A competitive game opens on its forecast, the stakes inside
 * it when the read sends them; **a For-fun game never draws a forecast** (ADR-0207 §5), even if a
 * read sent one — the deck card's rule (`headlineOf`) read on the details. Nothing where the read
 * could not forecast the game: the stakes are drawn inside the forecast or not at all.
 */
export function topCardOf(
  details: Pick<ProposalDetails, 'kind' | 'forecast' | 'atStake'>,
): DetailsTopCard | undefined {
  if (details.kind !== 'competitive' || details.forecast === undefined) return undefined;
  return {
    kind: 'forecast',
    forecast: details.forecast,
    ...(details.atStake === undefined ? {} : { atStake: details.atStake }),
  };
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
