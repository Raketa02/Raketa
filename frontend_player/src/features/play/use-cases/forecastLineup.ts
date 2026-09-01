/**
 * What a four you composed would leave on court — **and the one thing this file refuses to
 * do, which is arithmetic.**
 *
 * `ForecastResponse` returns *"three arrangements of a four you composed"*, each with its own
 * forecast, so what crosses is every answer the builder could need and what the client does
 * with it is **choose**. `the-play-screens.md` §11.3: *"no forecast arithmetic — the client
 * selects among arrangements and renders numbers it was given"*, and the check for it is
 * looking for arithmetic rather than reading intent. There is none here and none in
 * `domain/forecast`.
 *
 * **It records nothing and there is no id to read it back by.** Nothing was searched, so the
 * answer is a pure function of `(search_id, the set of players)` — which is exactly the shape
 * of a Query key, and why this is read rather than mutated
 * (`hooks/searchKeys.ts`, [ADR-0108](../../../../../docs/adr/0108-a-forecast-is-a-route-not-a-search.md)).
 *
 * **The two version stamps are dropped**, and that is a decision rather than an omission: the
 * builder draws no footer, `SH.whyfit`'s versions come off the search envelope that ranked
 * the row it is explaining, and a forecast's own pair would be a second answer to *which
 * ruleset* on one screen. They come back the day something prints them.
 */

import { requestForecast } from '../api/playSearchApi';
import type { Arrangement } from '../domain/forecast';
import {
  toForecastArrangements,
  toForecastRequest,
  type ForecastAsk,
} from '../mappers/forecastMappers';

export type { ForecastAsk };

export interface ForecastPorts {
  /** Query's own, so a forecast nobody is waiting for stops costing the socket. */
  readonly signal?: AbortSignal;
}

export function forecastLineup(
  ask: ForecastAsk,
  { signal }: ForecastPorts = {},
): Promise<readonly Arrangement[]> {
  return requestForecast(toForecastRequest(ask), { signal }).then(toForecastArrangements);
}
