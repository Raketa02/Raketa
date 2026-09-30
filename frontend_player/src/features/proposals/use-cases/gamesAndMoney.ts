/**
 * **Games & money, read and saved** (#554) — pass-throughs, the uniform-strict escape hatch: the
 * ranges are the server's, and a value it does not offer is refused there with a code naming what
 * it offers. The one rule the screen needs, how a tap moves a value inside the range, is
 * `domain/gamesAndMoney`.
 */

import { getGamesAndMoney, putGamesAndMoney, type Cancellable } from '../api/proposalsApi';
import type { GamesAndMoney, Limits } from '../domain/gamesAndMoney';
import { toGamesAndMoney, toGamesAndMoneyRequest } from '../mappers/gamesAndMoneyMappers';

export async function readGamesAndMoney(options: Cancellable = {}): Promise<GamesAndMoney> {
  return toGamesAndMoney(await getGamesAndMoney(options));
}

/** Save both limits. Answers what is now saved, with the form's offer as it stands. */
export async function saveGamesAndMoney(limits: Limits): Promise<GamesAndMoney> {
  return toGamesAndMoney(await putGamesAndMoney(toGamesAndMoneyRequest(limits)));
}
