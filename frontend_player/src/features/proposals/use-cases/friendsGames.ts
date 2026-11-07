/**
 * **A friends game's writes** — sent, accepted, declined, called off
 * ([#759](https://github.com/Raketa02/Raketa/issues/759)); a friend invited into an empty seat, and
 * the seat opened to the group ([#760](https://github.com/Raketa02/Raketa/issues/760)).
 * Pass-throughs over the wire: what each answer means is the domain's (`friendsGame.ts`) and the
 * screens'.
 */

import {
  postCallOff,
  postFriendsGame,
  postInvitationAcceptance,
  postInvitationDecline,
  postSeatInvitation,
  postSeatOpening,
} from '../api/proposalsApi';
import type { FriendsGameAccepted, FriendsGameSend, FriendsGameSent } from '../domain/friendsGame';
import {
  toFriendsGameAccepted,
  toFriendsGameSent,
  toSendFriendsGameRequest,
} from '../mappers/friendsGameMappers';

export async function sendFriendsGame(
  groupId: string,
  send: FriendsGameSend,
): Promise<FriendsGameSent> {
  return toFriendsGameSent(await postFriendsGame(groupId, toSendFriendsGameRequest(send)));
}

export async function acceptFriendsGame(bookingId: string): Promise<FriendsGameAccepted> {
  return toFriendsGameAccepted(await postInvitationAcceptance(bookingId));
}

export function declineFriendsGame(bookingId: string): Promise<void> {
  return postInvitationDecline(bookingId);
}

export function callOffFriendsGame(bookingId: string): Promise<void> {
  return postCallOff(bookingId);
}

export function inviteIntoASeat(
  bookingId: string,
  seatOf: string,
  friendId: string,
): Promise<void> {
  return postSeatInvitation(bookingId, seatOf, { friend_id: friendId });
}

export function openASeat(bookingId: string, seatOf: string): Promise<void> {
  return postSeatOpening(bookingId, seatOf);
}
