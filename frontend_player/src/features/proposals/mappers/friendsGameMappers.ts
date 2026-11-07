/**
 * **A friends game's writes, off and onto the wire** — the send's body and its answer, and an
 * accept's answer ([#759](https://github.com/Raketa02/Raketa/issues/759), over #751's routes).
 */

import { toWireSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';
import type { Sport } from '@/shared/vocabulary/sport';

import type { YourPayment } from '../domain/fill';
import type { FriendsCardAsk, FriendsCourtPick } from '../domain/friendsCard';
import type { PayMode } from '../domain/vocabulary';

import { toWireKind } from './deckMappers';
import { toYourPayment } from './fillMappers';

type Schemas = components['schemas'];

/**
 * **What a send asks** — the card as it was read (the line-up, the sides sent, the court it names)
 * and how to pay; with `bookingId`, the send again after its payments were confirmed.
 */
export interface FriendsGameSend {
  readonly sport: Sport;
  readonly ask: FriendsCardAsk;
  /** The court the card names — its own, or the one picked in *Find a court*. */
  readonly court: FriendsCourtPick;
  readonly payMode: PayMode;
  readonly bookingId?: string;
}

/** **What a send did** — the court booked, or nothing booked and the payments to confirm. */
export interface FriendsGameSent {
  readonly bookingId: string;
  readonly booked: boolean;
  readonly yourPayments: readonly YourPayment[];
}

/** **What an *Accept* did** — the reader In (and the game whole), or their share refused. */
export interface FriendsGameAccepted {
  readonly bookingId: string;
  readonly accepted: boolean;
  /** Every seat is taken now — *It's a game!*. */
  readonly whole: boolean;
  readonly yourPayment?: YourPayment;
}

export function toSendFriendsGameRequest(send: FriendsGameSend): Schemas['SendFriendsGameRequest'] {
  return {
    sport: toWireSport(send.sport),
    kind: toWireKind(send.ask.kind),
    friend_ids: [...send.ask.friendIds],
    partner_id: send.ask.partnerId ?? null,
    court_id: send.court.courtId,
    starts_at: send.court.startsAt,
    pay_mode: send.payMode,
    booking_id: send.bookingId ?? null,
  };
}

export function toFriendsGameSent(wire: Schemas['FriendsGameSentResponse']): FriendsGameSent {
  return {
    bookingId: wire.booking_id,
    booked: wire.booked !== null,
    yourPayments: wire.your_payments.map(toYourPayment),
  };
}

export function toFriendsGameAccepted(
  wire: Schemas['FriendsGameAnswerResponse'],
): FriendsGameAccepted {
  return {
    bookingId: wire.booking_id,
    accepted: wire.accepted,
    whole: wire.whole,
    ...(wire.your_payment === null ? {} : { yourPayment: toYourPayment(wire.your_payment) }),
  };
}
