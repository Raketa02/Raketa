/**
 * **The moment a yes may fill a game** — which yes waits ten seconds behind *Undo*, what the
 * server's answer to a yes means, and who *It's a game!* draws
 * ([#555](https://github.com/Raketa02/Raketa/issues/555); the mechanics §6.5, §11, §12.2; the
 * screens A2.4).
 *
 * Pure. **Whether a game filled is the server's to say** — the last yes books it inside its own
 * transaction, everyone paid or nobody did (#541) — so nothing here predicts a fill. What the client
 * decides is only the ten seconds in front of a yes that would move money, and what to put on the
 * phone once the answer is back.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import { chargesAtOnce, type DeckCard, type DeckPerson } from './deck';
import { deadlineOf, type Deadline, type SeatAtStake } from './home';
import type { LiveYes } from './liveYes';
import type { GameKind, PaymentRefusal, TimeTo } from './vocabulary';

/**
 * **What a yes is said on** — a dealt card, a game's details, a rescue's details or a *Seats to fill*
 * row (#557): the id the yes is sent for (a rescue's is its booking's), whether it waits behind
 * *Undo*, and the sides *It's a game!* draws. **A row holds no sides** — it lists the players, not
 * which side the open seat is on — so its faces are read off the booking once the seat is taken.
 */
export interface YesOn extends Pick<DeckCard, 'proposalId' | 'type' | 'court'> {
  readonly sides?: DeckCard['sides'];
}

/** **The deck a card was dealt in** — a group's, for one sport and one kind: what an answer re-reads. */
export interface DealtIn {
  readonly groupId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
}

// ---------------------------------------------------------------------------
// Undo
// ---------------------------------------------------------------------------

/** *Booking in 10 s* — every action that moves money waits this long (the mechanics §6.5). */
export const UNDO_WINDOW_MS = 10_000;

/**
 * **Whether a yes on this card waits behind *Undo*** — a yes on *Book it now*, which fills the game
 * and charges everyone, and **every** rescue join, which pays at once (Q74). Any other yes is a
 * free vote, sent at once and withdrawn free from *You're In*. It is the yes that charges at once,
 * the one that says *Pay* (`chargesAtOnce`, Q124), read through one rule so what counts ten seconds
 * and what says *Pay* cannot drift apart.
 */
export function waitsForUndo(card: Pick<DeckCard, 'type' | 'court'>): boolean {
  return chargesAtOnce(card);
}

/**
 * **A rescue** — a booked game's open seat (#545): its id is the booking's, a yes takes the seat and
 * pays at once (`POST /bookings/{id}/seats`) and a no is the booking's too.
 */
export function isRescue(card: Pick<DeckCard, 'type'>): boolean {
  return card.type === 'SEAT_OPEN';
}

/**
 * **Whose seat a refused yes leaves at stake** — a rescue's, kept for the player to take (#640), when
 * the yes was said on one; the player's own otherwise. A *TO CONFIRM* row holds no card, so it reads
 * as their own: the read does not say which it is.
 */
export function seatAtStake(card: Pick<YesOn, 'type'> | undefined): SeatAtStake {
  return card !== undefined && isRescue(card) ? 'aRescue' : 'yours';
}

/**
 * **What the fill holds for a rescue's *I'm in*** — from its details seen from outside, or a *Seats to
 * fill* row: the booking's seat, waiting behind *Undo* as every rescue join does (Q74), with the
 * sides when the surface holds them.
 */
export function yesOnRescue(rescue: {
  readonly bookingId: string;
  readonly sides?: DeckCard['sides'];
}): YesOn {
  return {
    proposalId: rescue.bookingId,
    type: 'SEAT_OPEN',
    court: 'BOOKED',
    ...(rescue.sides === undefined ? {} : { sides: rescue.sides }),
  };
}

/**
 * **The toast's count** — whole seconds until `endsAt`, **rounded up**, so the toast says *1 s*
 * through the last second and never *0 s* while the yes can still be taken back.
 */
export function undoSecondsLeft(endsAt: number, now: number): number {
  return Math.max(0, Math.ceil((endsAt - now) / 1_000));
}

// ---------------------------------------------------------------------------
// The answer
// ---------------------------------------------------------------------------

/** The booking a yes made, and the ordinary Game it opened. */
export interface Booked {
  /** The proposal's own id — one id from the first card to the court (#541). */
  readonly bookingId: string;
  readonly gameId: string;
}

/**
 * This player's share, refused when the game filled, or when they went for a rescue's seat: nobody paid, and the seat is theirs alone for their time (Q109, #640) — open to
 * others too once it ran out.
 */
export interface YourPayment {
  readonly seatChargeId: string;
  readonly refusal: PaymentRefusal;
  /**
   * **Their time** (#625, #626) — *Confirm your payment by 14:40 to keep your seat*. Absent once it
   * ran out, where none was given, and from an older server.
   */
  readonly confirmBy?: string;
  /**
   * **What it is for** (#638; Q113) — to fix the card, before the club's cut-off, where nothing is
   * paid now; or to pay, after it. With `confirmBy`; absent from an older server, which read as
   * the time to pay.
   */
  readonly timeTo?: TimeTo;
}

/** What a yes left on the game — `POST /proposals/{id}/yes`, and the payment confirmation's answer. */
export interface YesAnswer {
  readonly proposalId: string;
  /** Seats nobody is In on yet, this yes counted. */
  readonly openSeats: number;
  /** This yes booked the game. */
  readonly booked: Booked | null;
  /** This player's share could not be held. */
  readonly yourPayment: YourPayment | null;
  /**
   * **This yes filled the game, and a share was refused** (#625, #626; Q110) — the game waits for
   * that payment until then: somebody else's, or this player's own (`yourPayment`). Absent on every
   * other answer, and from an older server.
   */
  readonly paymentAwaitedUntil?: string;
}

/**
 * **What the phone does with a yes's answer.**
 *
 * - `booked` — this yes filled the game, everybody paid: *It's a game!*, for this player alone.
 * - `confirm` — their share needs them: the bank wants to check it, or declined it. *Your payment
 *   didn't go through — confirm it to keep your seat*, and the confirmation on the same payment,
 *   naming their time to pay when they have one (Q109). **It comes before a payment awaited**: a
 *   refusal of the player's own is no screen, only their sheet (Q110).
 * - `setUp` — no method at the fill: save one, and the yes again.
 * - `termsAgain` — the card's brand changed; its terms are accepted again on You › Payments.
 * - `paymentAwaited` — this yes filled the game and somebody else's share was refused (#625; Q110): nobody
 *   paid, and the game is on Home *waiting for one payment* until `until`, by the booking's id — the
 *   proposal's own. *It's a game!*, for this player alone, with what is still missing. When the
 *   payment comes in the others are told *booked · 40 zł held*, never a second *It's a game!*.
 * - `counted` — a vote, as every other: seats still open.
 */
export type FillOutcome =
  | { readonly kind: 'booked'; readonly bookingId: string }
  | { readonly kind: 'paymentAwaited'; readonly bookingId: string; readonly until: string }
  | ({ readonly kind: 'confirm' } & Confirmation)
  | { readonly kind: 'setUp' }
  | { readonly kind: 'termsAgain' }
  | { readonly kind: 'counted' };

/** The outcomes a refused yes can also come to — the two only the fill can mend. */
export type FillRefusal = Extract<FillOutcome, { readonly kind: 'setUp' | 'confirm' }>;

/**
 * **A refused yes the fill mends itself** — `payment_method_required`, a yes with nothing saved
 * (the setup, and the yes again), and `payment_to_confirm`, a yes on a game where a refused share of
 * this player's waits (the confirmation, on the payment `details.seat_charge_id` names). Any other
 * refusal — or one naming no payment — is the screen's to say.
 */
export function fillRefusal(
  code: string | undefined,
  details: Readonly<Record<string, unknown>> | undefined,
): FillRefusal | undefined {
  if (code === 'payment_method_required') return { kind: 'setUp' };
  const seatChargeId = details?.seat_charge_id;
  if (code === 'payment_to_confirm' && typeof seatChargeId === 'string') {
    return { kind: 'confirm', seatChargeId };
  }
  return undefined;
}

export function fillOutcome(answer: YesAnswer): FillOutcome {
  if (answer.booked !== null) return { kind: 'booked', bookingId: answer.booked.bookingId };
  const refused = answer.yourPayment;
  if (refused === null) {
    const until = answer.paymentAwaitedUntil;
    return until === undefined
      ? { kind: 'counted' }
      : { kind: 'paymentAwaited', bookingId: answer.proposalId, until };
  }
  switch (refused.refusal) {
    case 'AUTHENTICATION_REQUIRED':
    case 'DECLINED':
      return { kind: 'confirm', ...confirmationOf(refused) };
    case 'NO_METHOD':
      return { kind: 'setUp' };
    case 'TERMS_NEEDED':
      return { kind: 'termsAgain' };
  }
}

/**
 * **A refused share to confirm** — the payment the confirmation opens on, and the player's time
 * while one runs (Q109) and what it is for (Q113), which the sheet names. What every opener hands
 * the fill: the yes's answer, a *TO CONFIRM* row, a game's details.
 */
export type Confirmation = Pick<YourPayment, 'seatChargeId' | 'confirmBy' | 'timeTo'>;

export function confirmationOf(payment: Confirmation): Confirmation {
  return {
    seatChargeId: payment.seatChargeId,
    ...(payment.confirmBy === undefined ? {} : { confirmBy: payment.confirmBy }),
    ...(payment.timeTo === undefined ? {} : { timeTo: payment.timeTo }),
  };
}

/**
 * **A share of this player's refused when its game filled, waiting for them** — `GET
 * /players/me/payments-to-confirm` (#541): a game whose seat is held for them while their time to
 * pay runs (#625, #626), or reopened once it ran out. What a live yes knows of its game, and the
 * payment.
 */
export interface PaymentToConfirm extends LiveYes {
  readonly seatChargeId: string;
  /** Only the two that wait for the player: the bank's check, or a decline. */
  readonly refusal: Extract<PaymentRefusal, 'AUTHENTICATION_REQUIRED' | 'DECLINED'>;
  /**
   * **Their time** (Q109) — *Confirm your payment by 14:40*. Absent once it ran out: the row stays,
   * without a time, while the seat is still free to take back.
   */
  readonly confirmBy?: string;
  /** What it is for (Q113) — *Fix your card by 14:40* before the cut-off. With `confirmBy`. */
  readonly timeTo?: TimeTo;
}

/**
 * **The reader's refused share on one game** — a booked game's details offer its confirmation. A
 * booking takes its proposal's id (#541), so the row for the game Home opens is found by it.
 */
export function paymentToConfirmOn(
  bookingId: string,
  payments: readonly PaymentToConfirm[] | undefined,
): PaymentToConfirm | undefined {
  return payments?.find((payment) => payment.proposalId === bookingId);
}

// ---------------------------------------------------------------------------
// It's a game!
// ---------------------------------------------------------------------------

/** One face on *It's a game!* — the whole nickname for the sentence, the photograph when there is one. */
export interface Face {
  readonly playerId: string;
  /** Absent for an account that can no longer be named. */
  readonly name?: string;
  readonly photoUrl?: string;
}

/** The two sides, yours first and you first within it. */
export interface ItsAGamePicture {
  readonly yours: readonly Face[];
  readonly theirs: readonly Face[];
}

/**
 * **Who *It's a game!* draws** — the card the yes was said on, whose rows are the sides (Q70): your
 * side with you first, `vs`, the other. The card is the reader's own version, the one the last yes
 * filled, so its sides are the ones the booking drew (#541: *the deck's evenest*).
 */
export function itsAGamePicture(card: Pick<DeckCard, 'sides'>): ItsAGamePicture {
  const you = card.sides.yours.filter((person) => person.isYou);
  const partners = card.sides.yours.filter((person) => !person.isYou);
  return { yours: [...you, ...partners].map(faceOf), theirs: card.sides.theirs.map(faceOf) };
}

function faceOf(person: DeckPerson): Face {
  return {
    playerId: person.playerId,
    ...(person.name === undefined ? {} : { name: person.name }),
    ...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl }),
  };
}

/**
 * **What *It's a game!* says is still missing**, in one line under the word — one payment (Q110),
 * and until when: *Waiting for one payment · until 14:40 · Nobody pays until it's in*. Never whose.
 * Nothing is missing when every share held, and there is no line: a full game books at once at
 * every club (ADR-0196, #676). The answer to the yes names the time (`paymentAwaitedUntil`), so
 * nothing is read; it is written as Home writes it, the hour alone when it falls on `now`'s day.
 */
export interface ItsAGamePaymentAwaited {
  readonly until: Deadline;
}

export function aPaymentAwaited(until: string, now: number): ItsAGamePaymentAwaited {
  return { until: deadlineOf(until, now) };
}
