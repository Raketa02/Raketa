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

import type { DeckCard, DeckPerson } from './deck';
import type { LiveYes } from './liveYes';
import type { GameKind, PaymentRefusal } from './vocabulary';

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
 * and charges everyone, and **every** rescue join, which pays at once (Q74). At an On request club
 * a *Book it now* yes waits too: at zero the game goes to the club, and the charge follows its
 * confirmation (A2.4). Any other yes is a free vote, sent at once and withdrawn free from *You're
 * In*.
 */
export function waitsForUndo(card: Pick<DeckCard, 'type' | 'court'>): boolean {
  return card.type === 'SEAT_OPEN' || card.court === 'BOOK_IT_NOW';
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

/** This player's share, refused when the game filled: nobody paid, and their seat is open again. */
export interface YourPayment {
  readonly seatChargeId: string;
  readonly refusal: PaymentRefusal;
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
}

/**
 * **What the phone does with a yes's answer.**
 *
 * - `booked` — this yes filled the game, everybody paid: *It's a game!*, for this player alone.
 * - `confirm` — their share needs them: the bank wants to check it, or declined it. *Your payment
 *   didn't go through — confirm it to keep your seat*, and the confirmation on the same payment.
 * - `setUp` — no method at the fill: save one, and the yes again.
 * - `termsAgain` — the card's brand changed; its terms are accepted again on You › Payments.
 * - `counted` — a vote, as every other: seats still open, somebody else's share refused, or a full
 *   game an On request club has still to confirm.
 */
export type FillOutcome =
  | { readonly kind: 'booked'; readonly gameId: string }
  | { readonly kind: 'confirm'; readonly seatChargeId: string }
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
  if (answer.booked !== null) return { kind: 'booked', gameId: answer.booked.gameId };
  const refused = answer.yourPayment;
  if (refused === null) return { kind: 'counted' };
  switch (refused.refusal) {
    case 'AUTHENTICATION_REQUIRED':
    case 'DECLINED':
      return { kind: 'confirm', seatChargeId: refused.seatChargeId };
    case 'NO_METHOD':
      return { kind: 'setUp' };
    case 'TERMS_NEEDED':
      return { kind: 'termsAgain' };
  }
}

/**
 * **A share of this player's refused when its game filled, waiting for them** — `GET
 * /players/me/payments-to-confirm` (#541): a game still filling whose seat reopened on it. What a
 * live yes knows of its game, and the payment.
 */
export interface PaymentToConfirm extends LiveYes {
  readonly seatChargeId: string;
  /** Only the two that wait for the player: the bank's check, or a decline. */
  readonly refusal: Extract<PaymentRefusal, 'AUTHENTICATION_REQUIRED' | 'DECLINED'>;
}

// ---------------------------------------------------------------------------
// It's a game!
// ---------------------------------------------------------------------------

/** One face on *It's a game!* — the whole Name for the sentence, the photograph when there is one. */
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
