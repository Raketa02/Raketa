/**
 * The court's pairing, as the app talks about it — **or the route's word that there is none.**
 *
 * A pass-through with a mapping, on `readGames`' escape hatch, plus the one fold this read owns:
 * the route's three named refusals are **answers**, not failures. *No game of yours has that id*,
 * *the game has happened* and *the account is held* each mean there is no pairing to draw, and
 * #410 decided the block says nothing about which — so the read resolves to `null` for all three
 * rather than rejecting, and the hook over it holds *no pairing* as data rather than as an error
 * to retry on every focus. `null` and not `undefined`, because Query refuses `undefined` as a
 * query's answer, and this is one.
 *
 * Anything else is the failure it is and reaches the hook as one, where the app's own retry rule
 * decides what to do with it.
 */

import { isAppError } from '@/shared/errors';

import type { Cancellable } from '../api/gamesApi';
import { getPairing } from '../api/pairingApi';
import { pairingRefusedByName, type Pairing } from '../domain/pairing';
import { toPairing } from '../mappers/pairingMappers';

export function readPairing(gameId: string, options: Cancellable = {}): Promise<Pairing | null> {
  return getPairing(gameId, options).then(toPairing, (error: unknown) => {
    if (isAppError(error) && pairingRefusedByName(error)) return null;
    throw error;
  });
}
