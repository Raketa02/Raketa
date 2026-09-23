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
 * ## And it is the same act again on a court somebody else built
 *
 * ⚡ pressed on a challenge is this use-case with the other ask
 * ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)):
 * the request **names the challenge and says nothing else about the court**, because the sport,
 * the kind of evening and the locked seats are all read off it — and the gate steps aside for
 * that one challenge, so the people who accepted come back as ordinary rows the builder can
 * draw. What differs on this side is only what the *record* is stamped with, which is
 * `challengeOrigin` below and nothing else: the same mint, the same court, the same rebinding.
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

import { unknownFailure } from '@/shared/errors';
import type { Sport } from '@/shared/vocabulary/sport';

import { runLineup } from '../api/playSearchApi';
import type { SearchEnvelope } from '../domain/candidate';
import type { SeatedCourt } from '../domain/forecast';
import type { CompletingChallenge, PlayOrigin, SearchRecord } from '../domain/lineup';
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
export type FillSeatsAsk = FillTheCourtYouComposed | FinishTheCourtSomebodyBuilt;

/** ⚡ on a court composed in Play, empty or part-seated. The origin is already known. */
export interface FillTheCourtYouComposed {
  readonly kind: 'search';
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
 * ⚡ on a **challenge** — the half-built court somebody else's send left standing.
 *
 * It carries the challenge and the sport and nothing else, because everything else about the
 * court is the challenge's: the request says only which challenge, and the *record* needs a
 * sport because `SearchEnvelope` has never carried one.
 *
 * **No `quotes`, and therefore no prompts.** The four prompts are about the searcher's own
 * *Find a game* values — a week they improvised, a radius they widened, a sport they have not
 * declared — and this journey composes none of them: the press is on a court somebody else
 * built, and the answer is pushed away from in the same beat, so a sheet raised here would
 * stand in front of a screen that is already gone. Dismissal is *not now* and *not now*
 * suppresses for thirty days, so asking here would **spend** the offer on the one surface that
 * cannot honour it — `answerableWithoutAWeekGrid`'s own argument, one screen over.
 */
export interface FinishTheCourtSomebodyBuilt {
  readonly kind: 'challenge';
  readonly completing: CompletingChallenge;
  /** The challenge's own sport. The **record** is stamped with it; the request never carries it. */
  readonly sport: Sport;
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
    toRunLineupRequest(
      ask.kind === 'challenge'
        ? { completing: ask.completing.challengeId, sentWeek: undefined }
        : {
            sport: ask.origin.sport,
            mode: ask.origin.mode,
            lockedSeats: ask.lockedSeats,
            sentWeek: ask.sentWeek,
          },
    ),
  );

  const { envelope, candidates, court } = toLineupAnswer(response);
  const origin = ask.kind === 'challenge' ? challengeOrigin(ask, envelope) : ask.origin;

  return {
    // The origin is folded on here for `toOriginSearch`'s reason — the envelope carries the id
    // and the mode and neither the sport nor the week, because those were the request's.
    record: { ...toOriginSearch(response, origin), envelope, candidates, court },
    playersInRange: envelope.pool.playersInRange,
    prompts:
      ask.kind === 'challenge'
        ? []
        : answerableWithoutAWeekGrid(toRaisedPrompts(response, ask.quotes)),
  };
}

/**
 * The origin a challenge fill is stamped with — **read back off the answer, because that is the
 * only place two of its three facts exist.**
 *
 * The request said only which challenge, so the record has to learn the rest from what came
 * back: the **mode** is the one the engine resolved — inherited from a challenge that was sent
 * with one, or read off the filler's own declared Play intent where it was not (ADR-0150 §5) —
 * and it is on the envelope like every other fact about this answer. The **sport** is the
 * challenge's and is the ask's, for `SearchEnvelope`'s standing reason: it has never carried
 * one. The **week** is absent, which is *the profile's own grid* and is exactly what was asked.
 *
 * **A line-up answer with no mode is refused rather than bound.** `SearchEnvelope.mode` is null
 * *exactly on the deck*, and this route is not the deck — so a null here is an answer no
 * forecast could ever be asked under, `ForecastRequest.mode` being required. Inventing one is
 * the one failure that would not show: every arrangement on the court would silently be priced
 * under a weight vector nobody chose.
 */
function challengeOrigin(ask: FinishTheCourtSomebodyBuilt, envelope: SearchEnvelope): PlayOrigin {
  if (envelope.mode === null) throw unknownFailure('a line-up answer carried no mode');
  return { sport: ask.sport, mode: envelope.mode, completing: ask.completing };
}
