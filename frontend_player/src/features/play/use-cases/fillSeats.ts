/**
 * ⚡ **Let the engine fill the seats** — one request, one recorded search, and a whole court.
 *
 * ## It is the same act on an empty court and on a half-built one
 *
 * `RunLineupRequest` says so in its own docstring: the line-up and fill-seats *"differ by
 * `locked_seats` being non-empty, which is a property of what you send rather than of where
 * you send it — so hand-seating somebody and pressing ⚡ is the same shape as ⚡ on an empty
 * court, and there is no second route for a client to get wrong."* This use-case is that
 * sentence: the ask carries whoever is already seated, and nothing branches on how many.
 *
 * **From the first locked seat the engine optimises for the group**, and the answer says so in
 * `search.optimised_for`. That is not a detail the client derives from having sent a
 * `locked_seats` list — it is read off the envelope, so a read-back a month later still says
 * what it was.
 *
 * ## The answer is a new record, and the line-up rebinds to it
 *
 * `POST /lineups` **mints a search**. So the four it seats came off *that* search's rows, and
 * the line-up the builder now holds is `{ originSearchId: the new id, seats }` — which is what
 * makes the forecast on the next swap askable at all, since `POST /forecasts` refuses anybody
 * who did not appear in the search it cites. A fill that kept the old origin would be a
 * line-up whose members the origin cannot vouch for, discovered at the first membership
 * change.
 *
 * ## What it does not do
 *
 * **It does not write the radius.** `RunLineupRequest` has none for the shortlist's reason,
 * and the builder draws no slider — the radius was settled on Find a game, which is where the
 * one act with two requests lives (`findAGame`).
 *
 * ## It carries the prompts back, minus the one the builder cannot answer
 *
 * A line-up raises them like a search does, and `SH.saveav`
 * ([#275](https://github.com/Raketa02/Raketa/issues/275)) is the sheet that answers one. It
 * now exists, so the list is carried ([#287](https://github.com/Raketa02/Raketa/issues/287)).
 *
 * **`REFRESH_YOUR_TIMES` is dropped rather than drawn**, for the reason `dealDeck` drops it:
 * its *yes* is a request for the week grid, ⚡ lands on the court the player is already looking
 * at, and a question whose only answer would be a screen this one does not have costs the
 * screen that **does** have it thirty days of silence — dismissal is *not now*, and *not now*
 * suppresses. `answerableWithoutAWeekGrid` is the one place that is decided.
 */

import { runLineup } from '../api/playSearchApi';
import type { SeatedCourt } from '../domain/forecast';
import type { PlayOrigin, SearchRecord } from '../domain/lineup';
import { answerableWithoutAWeekGrid, type RaisedPrompt } from '../domain/raisedPrompt';
import { toLineupAnswer, toRunLineupRequest } from '../mappers/forecastMappers';
import { toOriginSearch, toRaisedPrompts, type PromptQuotes } from '../mappers/searchMappers';
import type { SeatedPlayerId } from '../domain/lineup';

/**
 * What ⚡ is pressed with.
 *
 * It carries the **origin** where the mapper's `LineupAsk` carries a sport and a mode, and the
 * difference is the point: the sport and the mode are what the *request* needs, and the origin
 * is what the *record* is stamped with — `SearchEnvelope` carries neither the sport nor the
 * week, so a line-up's validity could not be judged without folding them back on.
 */
export interface FillSeatsAsk {
  /** What the builder is filling **for** — and what the new record is stamped with. */
  readonly origin: PlayOrigin;
  /** Whoever is already on the court, in seat order. Empty is ⚡ on an empty court. */
  readonly lockedSeats: readonly SeatedPlayerId[];
  /** The improvised week, or `undefined` to fill against the grid the profile holds. */
  readonly sentWeek: PlayOrigin['week'] | undefined;
  /**
   * The two facts a raised prompt's sentence quotes and the response does not carry.
   *
   * `profileWeek` is statable as **absent** here where Find a game's never is: ⚡ is pressed on
   * a court whose record came out of the cache, and the profile read behind it may not have
   * landed. An absent week drops the prompt that would have quoted it rather than drawing a
   * diff against one nobody holds (`mappers/searchMappers`).
   */
  readonly quotes: PromptQuotes;
}

/**
 * The record the fill minted, and the one number its latch prints.
 *
 * `playersInRange` rides beside the record rather than inside it for `SearchOutcome`'s reason:
 * it is a fact about **this answer** and not about the record a line-up is judged against, and
 * a count re-read months later would describe a pool that has moved.
 */
export interface FillSeatsOutcome {
  /**
   * **A line-up answer always has a court**, which is why the record's optional field is
   * required here: `SearchRecord` is the shape a shortlist is held in too, and a shortlist
   * seats nobody. A fill that seated nobody is *this shape with fewer people in it* — every
   * seat carrying a reason — and never a missing court, so the caller needs no branch for a
   * state the contract does not have.
   */
  readonly record: SearchRecord & { readonly court: SeatedCourt };
  readonly playersInRange: number;
  /**
   * The questions this fill raised, **already filtered to the ones this screen can answer.**
   *
   * Beside the count rather than inside the record, for the count's own reason: it is a fact
   * about **this answer** and not about the record a line-up is judged against, and a question
   * re-read months later would be asked about a value that has since moved — which is why the
   * wire omits prompts on a read-back at all.
   */
  readonly prompts: readonly RaisedPrompt[];
}

export async function fillSeats(ask: FillSeatsAsk): Promise<FillSeatsOutcome> {
  const response = await runLineup(
    toRunLineupRequest({
      sport: ask.origin.sport,
      mode: ask.origin.mode,
      lockedSeats: ask.lockedSeats,
      sentWeek: ask.sentWeek,
    }),
  );

  const { envelope, candidates, court } = toLineupAnswer(response);

  return {
    // The origin is folded on here for `toOriginSearch`'s reason — the envelope carries the id
    // and the mode and neither the sport nor the week, because those were the request's.
    record: { ...toOriginSearch(response, ask.origin), envelope, candidates, court },
    playersInRange: envelope.pool.playersInRange,
    prompts: answerableWithoutAWeekGrid(toRaisedPrompts(response, ask.quotes)),
  };
}
