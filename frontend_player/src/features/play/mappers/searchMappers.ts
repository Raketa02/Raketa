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
import { toWireSlots } from '@/features/player_profile/types';

import type { OriginSearch, PlayOrigin } from '../domain/lineup';
import type { RaisedPrompt } from '../domain/raisedPrompt';
import { SEARCH_MODES, type SearchMode } from '../domain/vocabulary';

type RunSearchRequest = components['schemas']['RunSearchRequest'];
type ShortlistResponse = components['schemas']['ShortlistResponse'];
type PromptSchema = components['schemas']['PromptSchema'];

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
}

export function toRunSearchRequest(ask: SearchAsk): RunSearchRequest {
  return {
    sport: toWireSport(ask.origin.sport),
    mode: ask.origin.mode,
    ...(ask.sentWeek === undefined ? {} : { availability_override: toWireSlots(ask.sentWeek) }),
  };
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
  /** How many cells the **profile's** week holds — `KEEP_THESE_TIMES`'s second number. */
  readonly slotsOnProfile: number;
}

/**
 * The questions this search raised, as sentences' worth of facts.
 *
 * **Present on a search and omitted on a read-back**, so an absent list is *this response did
 * not raise any* and never *this build could not read them*.
 *
 * `slotsWas` is the client's own count and the one value here the response does not carry: the
 * engine compares the **post-rung** grid the search actually ran on against the profile's, and
 * only it knows what the first of those was — so the wire sends `slots`, the count on the
 * profile is the read the screen already holds, and neither side computes the other's half.
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
            slotsNow: raised.slots.length,
            slotsWas: quoted.slotsOnProfile,
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
