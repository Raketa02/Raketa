/**
 * **Taking a rung** — a new search citing the one that offered it, and never a change to
 * anything saved.
 *
 * ## It is `POST /searches`, and the widening is not in the body
 *
 * `RunSearchRequest` carries `offered_by_search_id` and `rung`, and *"the widening itself is
 * **not** sent: the backend reads it off the offer it made."* So there is no radius here and
 * no added slot — the same reason there is no radius on an ordinary search, arriving a second
 * time: two sides holding an opinion about what a rung was worth is two sides that can
 * disagree, and only one of them ran the re-run that priced it
 * ([ADR-0099](../../../../../docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)).
 *
 * ## The origin is the same origin, and that is what makes this not a second search screen
 *
 * A rung relaxes an **ask**, not the question: the sport, the mode and the week the player
 * edited are all unchanged, so the record this mints carries the same `PlayOrigin` the offering
 * search did. That is what lets the pool re-bind to the widened list without the line-up guard
 * having anything to say — `sameOrigin` is true across the pair, and what actually changes is
 * the `search_id`, which is a different fact and the one `POST /forecasts` refuses on.
 *
 * **The week is sent exactly as the offering search sent it.** Unprovable is *sent*, which is
 * ⚡'s own rule for the same reason: a widened search that quietly ran on a different week from
 * the list above it would be the two disagreeing silently, and the caller is the only one who
 * knows whether the working copy still equals the profile's grid.
 *
 * ## No radius write, and that is the whole difference from *Search*
 *
 * Find a game's use-case writes the profile radius first, because the slider on that screen has
 * no other way to mean anything. Here the radius is the **engine's** number off an offer it
 * priced, and writing it would be exactly the conflation ADR-0099 exists to prevent: taking a
 * rung is one search, widening in You is every future search, and `KEEP_THIS_RADIUS` is the
 * hinge between them — asked **after** evidence, by the engine, and answered by a route this
 * client does not call from here.
 */

import { runSearch } from '../api/playSearchApi';
import type { PlayOrigin } from '../domain/lineup';
import type { Rung } from '../domain/vocabulary';
import { toRankedList } from '../mappers/candidateMappers';
import {
  toOriginSearch,
  toPlayersInRange,
  toRaisedPrompts,
  toRunSearchRequest,
  type PromptQuotes,
} from '../mappers/searchMappers';

import type { SearchOutcome } from './findAGame';

export interface TakeRungAsk {
  /** The offering search's own origin — a rung changes an ask, never the question. */
  readonly origin: PlayOrigin;
  /** The week the offering search ran on, or `undefined` where that was the profile's grid. */
  readonly sentWeek: PlayOrigin['week'] | undefined;
  /** The search that made the offer. It is the citation, and the route refuses any other. */
  readonly offeredBySearchId: string;
  readonly rung: Rung;
  /** The two facts a raised prompt's sentence quotes and the response does not carry. */
  readonly quotes: PromptQuotes;
}

export async function takeRung(ask: TakeRungAsk): Promise<SearchOutcome> {
  const response = await runSearch(
    toRunSearchRequest({
      origin: ask.origin,
      sentWeek: ask.sentWeek,
      taking: { offeredBySearchId: ask.offeredBySearchId, rung: ask.rung },
    }),
  );

  const { envelope, candidates } = toRankedList(response);

  return {
    // A shortlist seats nobody, so there is no `court` — the same absence a search from Find a
    // game leaves, and for the same reason.
    record: { ...toOriginSearch(response, ask.origin), envelope, candidates },
    playersInRange: toPlayersInRange(response),
    prompts: toRaisedPrompts(response, ask.quotes),
  };
}
