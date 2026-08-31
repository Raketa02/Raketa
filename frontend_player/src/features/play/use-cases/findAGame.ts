/**
 * Run a search for the ask on screen — **the radius first, where the radius moved.**
 *
 * ## Why two requests, and why in this order
 *
 * `RunSearchRequest` carries no radius and never will: the searcher's ask **is** their profile
 * radius, read at request time. So a slider on the search screen has exactly one way to mean
 * anything — the profile has to hold what the screen shows before the search is run — and a
 * screen that drew a distance the search did not use would be a control that lies quietly,
 * which is the same objection that keeps a sort nobody can act on off the pool.
 *
 * **It is one act with two requests rather than two acts.** The write is the first half of
 * pressing *Search*, so a failure in it is a search that has not happened: nothing was minted,
 * `retryTarget` answers *the-search*, and the retry is the control the player already pressed.
 * Sequencing it the other way — search, then save — would run the search at the old radius and
 * then quietly change the profile, which is the worst of both.
 *
 * **The write is skipped where nothing moved.** A `PUT` that lands the same state records
 * nothing, so this is politeness rather than correctness — but it also keeps *what a search
 * costs* honest: an unchanged radius is one request, which is what a player pressing search
 * twice should see.
 *
 * ## What this does not do
 *
 * **It does not write the week.** The working copy travels as `availability_override` and
 * nowhere else, *"so a week improvised for one evening is forgotten with the session"*; the
 * offer to keep it is `KEEP_THESE_TIMES`, which rides back on this response and is answered by
 * a different route entirely.
 *
 * **It does not write the mode.** The toggle is a `SearchMode` and the profile holds a
 * `PlayIntent`; ADR-0094's drift backstop exists precisely so those two are allowed to
 * disagree (`domain/playMode`).
 *
 * ## The radius write arrives as a port
 *
 * It is `player_profile`'s route, `player_profile`'s bounds and `player_profile`'s cache
 * effect — the response carries the radius **as the profile now holds it** after the range and
 * the step were re-checked, and something has to write that back. Reaching around that hook to
 * call the route directly would leave the profile read holding a number the server has already
 * corrected, so what Play supplies here is the act and never the endpoint.
 */

import { runSearch } from '../api/playSearchApi';
import type { OriginSearch, PlayOrigin } from '../domain/lineup';
import type { RaisedPrompt } from '../domain/raisedPrompt';
import {
  toOriginSearch,
  toRaisedPrompts,
  toRunSearchRequest,
  type PromptQuotes,
} from '../mappers/searchMappers';

export interface FindAGameAsk {
  readonly origin: PlayOrigin;
  /** The improvised week, or `undefined` where it still equals the profile's grid. */
  readonly sentWeek: PlayOrigin['week'] | undefined;
  /** What the slider shows, and what the profile holds — the write fires only if they differ. */
  readonly radiusKm: number;
  readonly profileRadiusKm: number;
  /** The two facts a raised prompt's sentence quotes and the response does not carry. */
  readonly quotes: PromptQuotes;
}

/**
 * The minted record, and the questions it raised.
 *
 * **The prompts ride on the response**, which is what makes *"it never blocks"* true by
 * construction rather than by a screen remembering to sequence a sheet after a request: by the
 * time there is anything to ask, the search has already run
 * ([#226](https://github.com/Raketa02/Raketa/issues/226) §6).
 */
export interface SearchOutcome {
  readonly origin: OriginSearch;
  readonly prompts: readonly RaisedPrompt[];
}

export interface FindAGamePorts {
  /** `player_profile`'s own radius write, with its cache effect attached. */
  readonly saveRadius: (radiusKm: number) => Promise<unknown>;
}

export async function findAGame(
  ask: FindAGameAsk,
  { saveRadius }: FindAGamePorts,
): Promise<SearchOutcome> {
  if (ask.radiusKm !== ask.profileRadiusKm) await saveRadius(ask.radiusKm);

  const response = await runSearch(
    toRunSearchRequest({ origin: ask.origin, sentWeek: ask.sentWeek }),
  );

  return {
    origin: toOriginSearch(response, ask.origin),
    prompts: toRaisedPrompts(response, ask.quotes),
  };
}
