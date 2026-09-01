/**
 * The search's wire boundary: the ask on the way out, and the questions it raises on the way
 * back.
 *
 * Two things cross here and neither is a renaming.
 *
 * **The ask is asks only, never facts about the searcher.** `RunSearchRequest` carries a
 * sport, a mode and — when the player edited it — the week, and *"there is deliberately no
 * radius here, and there never will be: a radius supplied by a phone is a gate evaluated on a
 * lie."* The searcher's radius, tags, rating, intent and gender preference are read from the
 * profile at request time. So this file has nothing to decide about them and no field to put
 * them in.
 *
 * **`availability_override` is omitted, never sent as `null`.** The contract says so in as many
 * words, and it is the same distinction the prompt's own payload draws one layer up: *omit* is
 * *use the grid on my profile*, and an **empty list** is *a cleared week*, which is a legal
 * edit and a legal thing to search on
 * ([#247](https://github.com/Raketa02/Raketa/issues/247)). Collapsing the two would make a
 * player who unticked every cell search on the week they were trying to leave behind.
 *
 * **A prompt is a code with a payload, and a payload it cannot quote is a prompt that is
 * dropped.** Every sentence `promptPresentation` writes quotes `RaisedPrompt`'s own values —
 * *"the value already in play, never a value the engine picked"* — so a `KEEP_THIS_RADIUS`
 * arriving with no radius on it has no sentence, and drawing it would mean inventing the
 * number it is asking about. That is [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md)
 * §3's **drop**: a prompt is an offer rather than a row in a count, so nothing is owed a gap
 * where one is missing.
 */

import type { components } from '@/generated/schema';
import { toWireSport } from '@/features/onboarding/types';
import { toWeekCells, toWireSlots } from '@/features/player_profile/types';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { OriginSearch, PlayOrigin } from '../domain/lineup';
import type { RaisedPrompt } from '../domain/raisedPrompt';
import { SEARCH_MODES, type Rung, type SearchMode } from '../domain/vocabulary';

type RunSearchRequest = components['schemas']['RunSearchRequest'];
type ShortlistResponse = components['schemas']['ShortlistResponse'];
type PromptSchema = components['schemas']['PromptSchema'];
type AvailabilitySlotResource = components['schemas']['AvailabilitySlotResource'];

/**
 * What Find a game asks for: the origin, and whether the week is the profile's.
 *
 * `sentWeek` decides the one field that is conditional. It is `undefined` where the working
 * copy still equals the profile's grid, which is what makes *"omit it, never send `null`"*
 * a decision the caller states rather than one this file infers from an empty array.
 */
export interface SearchAsk {
  readonly origin: PlayOrigin;
  /** The improvised week, or `undefined` to search on the grid the profile holds. */
  readonly sentWeek: PlayOrigin['week'] | undefined;
  /**
   * The offer this search accepts, where it is one — **the citation, and never the widening.**
   *
   * *"Taking a rung is a new search citing the one that offered it, never a silent change to
   * your saved preferences"*, and *"the widening itself is **not** sent: the backend reads it
   * off the offer it made"*. So there is no radius and no added slot in this shape, and there
   * is nowhere for one to be put — which is what stops the client and the engine holding two
   * opinions about what a rung was worth.
   *
   * Absent on an ordinary search, and the two fields travel as a pair because the contract
   * says so: `rung` is *"sent with `offered_by_search_id` or not at all"*.
   */
  readonly taking?: {
    readonly offeredBySearchId: string;
    readonly rung: Rung;
  };
}

export function toRunSearchRequest(ask: SearchAsk): RunSearchRequest {
  return {
    sport: toWireSport(ask.origin.sport),
    mode: ask.origin.mode,
    ...availabilityOverride(ask.sentWeek),
    ...(ask.taking === undefined
      ? {}
      : { offered_by_search_id: ask.taking.offeredBySearchId, rung: ask.taking.rung }),
  };
}

/**
 * **The week, or the field's absence** — written once, because three routes carry it.
 *
 * `POST /searches`, `POST /lineups` and `POST /deck` all say *"omit it, never send `null`"*,
 * and all three draw #247's distinction: an **omitted** override is *use the grid on my
 * profile*, and an **empty list** is *I unticked every cell*, which is a legal edit and a legal
 * thing to search on. Three copies of that conditional is three places for one of them to start
 * collapsing the two — and the collapse is silent, because it searches on a real week rather
 * than failing.
 *
 * The caller states which it is sending; nothing here infers it from an empty array.
 */
export function availabilityOverride(sentWeek: readonly WeekCell[] | undefined): {
  readonly availability_override?: AvailabilitySlotResource[];
} {
  return sentWeek === undefined ? {} : { availability_override: toWireSlots(sentWeek) };
}

/**
 * The record a line-up is judged against: **the id, and what it was asked for.**
 *
 * The origin is folded on here rather than read off the envelope because the envelope does not
 * carry it — `SearchEnvelope` has `search_id` and `mode` and neither the sport nor the week,
 * *"because those were the request's"*. That is what a DTO is for, and it is why *origin
 * search* is a name this app owns rather than a wire type.
 */
export function toOriginSearch(response: ShortlistResponse, origin: PlayOrigin): OriginSearch {
  return { searchId: response.search.search_id, origin };
}

/**
 * The one number a searching latch prints — post-gate, and never a number the client grew to
 * fill the time.
 *
 * `the-play-screens.md` §3 draws both lines this is on the right side of: the server never
 * delays to make a search feel substantial, and *"the count the animation prints is
 * `players_in_range` from the response."* §B14's *live* count was neither — it was
 * `len(generation.admitted)` on a 650 ms timer, printed before the answer existed
 * ([#223](https://github.com/Raketa02/Raketa/issues/223)) — so the count arrives here, off a
 * response, or it does not arrive at all.
 *
 * The rest of `PoolSchema` is deliberately left on the wire. `post_gate` travels *"so the
 * count cannot be misread"* and is always `true`; the radius and the window are the pool
 * header's and the deck's, and they come with the surfaces that draw them.
 */
export function toPlayersInRange(response: ShortlistResponse): number {
  return response.search.pool.players_in_range;
}

const KNOWN_MODES = new Set<SearchMode>(SEARCH_MODES);

/**
 * The two facts a prompt's sentence quotes that the response does not carry.
 *
 * They travel together everywhere — into the lift, into each arm, and on the ask the screen
 * builds — because they answer one question between them: *what does this build know that the
 * engine's payload does not*. The sport's name is this app's copy, and the count on the
 * profile is the read the screen already holds.
 */
export interface PromptQuotes {
  /** What this sport is called, for the one prompt whose sentence names it. */
  readonly sportName: string;
  /**
   * The **profile's** own week — `KEEP_THESE_TIMES`'s other half.
   *
   * The cells rather than their count, because the sheet draws the two weeks against each
   * other as a grid and quotes the count off the same list it draws
   * ([#275](https://github.com/Raketa02/Raketa/issues/275)).
   */
  readonly profileWeek: readonly WeekCell[];
}

/**
 * The questions this search raised, as sentences' worth of facts.
 *
 * **Present on a search and omitted on a read-back**, so an absent list is *this response did
 * not raise any* and never *this build could not read them*.
 *
 * The profile's week is the client's own and the one value here the response does not carry:
 * the engine compares the **post-rung** grid the search actually ran on against the profile's,
 * and only it knows what the first of those was — so the wire sends `slots`, the profile's
 * week is the read the screen already holds, and neither side computes the other's half.
 */
export function toRaisedPrompts(
  response: ShortlistResponse,
  quoted: PromptQuotes,
): readonly RaisedPrompt[] {
  return (response.search.prompts ?? []).flatMap((prompt) => toRaisedPrompt(prompt, quoted) ?? []);
}

function toRaisedPrompt(raised: PromptSchema, quoted: PromptQuotes): RaisedPrompt | undefined {
  switch (raised.prompt) {
    case 'KEEP_THESE_TIMES':
      // `undefined` is *not this prompt* and `[]` is *a cleared week* — two absences the
      // contract deliberately stopped conflating (#247), so `?? []` here would be this side
      // re-conflating them and offering to save a week nobody ran a search on.
      return raised.slots === undefined
        ? undefined
        : {
            prompt: 'KEEP_THESE_TIMES',
            // The same two named fields the profile's own week arrives in, read by the same
            // mapper (#286) — the sheet draws these cells and quotes their count, so one list
            // answers both and neither can disagree with the other.
            week: toWeekCells(raised.slots),
            profileWeek: quoted.profileWeek,
          };
    case 'KEEP_THIS_RADIUS':
      return raised.radius_km === undefined
        ? undefined
        : { prompt: 'KEEP_THIS_RADIUS', radiusKm: raised.radius_km };
    case 'UPDATE_PLAY_INTENT':
      return raised.mode === undefined || !KNOWN_MODES.has(raised.mode)
        ? undefined
        : { prompt: 'UPDATE_PLAY_INTENT', sportName: quoted.sportName, mode: raised.mode };
    case 'REFRESH_YOUR_TIMES':
      return { prompt: 'REFRESH_YOUR_TIMES' };
    // A code this build has never seen. Dropped rather than drawn as a gap: a prompt is an
    // offer, not a row in a total, so nothing on screen is left unaccounted for by its
    // absence (§3).
    default:
      return undefined;
  }
}
