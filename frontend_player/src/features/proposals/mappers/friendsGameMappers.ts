/**
 * **A friends game's writes, off and onto the wire** — the send's body and its answer, and an
 * accept's answer ([#759](https://github.com/Rakieta02/Rakieta/issues/759), over #751's routes).
 */

import { toWireSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';

import type { FriendsGameAccepted, FriendsGameSend, FriendsGameSent } from '../domain/friendsGame';

import { toWireKind } from './deckMappers';
import { toYourPayment } from './fillMappers';

type Schemas = components['schemas'];

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
