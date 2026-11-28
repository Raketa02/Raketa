/**
 * **Who turned up** — the four acts at a booked game's court
 * ([#658](https://github.com/Rakieta02/Rakieta/issues/658); ADR-0195 §3): *isn't here yet*, an arrival
 * (*I'm here* or *they're here*), *I was there* and *yes, they were here*.
 *
 * **Every answer is dropped**, for `stateResult`'s reason: each route replies with the game as it
 * now stands, folded against the server's clock, and splicing it into a list folded against an
 * older `read_at` would put two readings of the clock in one list. The caller invalidates, and the
 * next read is one fold over everything.
 *
 * **The position is a parameter and never a field of anything kept**: it is read at the tap by the
 * caller, handed straight to the request, and goes out of scope with it.
 */

import {
  postArrival,
  postNotHereYet,
  postPresenceClaim,
  postPresenceConfirmation,
} from '../api/gamesApi';
import type { TapPosition } from '../domain/attendance';
import {
  toArrivalRequest,
  toNotHereYetRequest,
  toPresenceConfirmationRequest,
} from '../mappers/gameMappers';

/** A tap about one player on one game — who, and nothing about the phone. */
export interface AboutAPlayer {
  readonly gameId: string;
  readonly playerId: string;
}

/** *Oscar isn't here yet*, made at `at`. */
export async function noteNotHereYet({ gameId, playerId }: AboutAPlayer, at: TapPosition) {
  await postNotHereYet(gameId, toNotHereYetRequest(playerId, at));
}

/** *I'm here* — the reader's own id — or *they're here*, somebody else's; made at `at`. */
export async function noteArrival({ gameId, playerId }: AboutAPlayer, at: TapPosition) {
  await postArrival(gameId, toArrivalRequest(playerId, at));
}

/** *I was there* — the reader's own, a day later at most, from anywhere. */
export async function claimPresence(gameId: string): Promise<void> {
  await postPresenceClaim(gameId);
}

/** *Yes, they were here* — about somebody else's claim. */
export async function confirmPresence({ gameId, playerId }: AboutAPlayer): Promise<void> {
  await postPresenceConfirmation(gameId, toPresenceConfirmationRequest(playerId));
}
