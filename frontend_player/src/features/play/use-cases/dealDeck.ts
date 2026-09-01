/**
 * Deal a deck — **one request, and the whole of what the screen asks for.**
 *
 * The deck is the search screen's opposite in every way that matters to a use-case. There is
 * no mode (*"the deck reads your own declared Play intent for the sport, resolved
 * backend-side"*), no radius (a deal runs on the profile's, and there is no slider to write
 * first), and no widening. What is left is a sport and — only where the player edited it — the
 * week, which is why this is one request where `findAGame` is two.
 *
 * ## The week travels the same way it does on a search, and for the same reason
 *
 * `availability_override` is **omitted rather than sent as `null`** where the working copy
 * still equals the profile's grid, and an **empty list is a cleared week**, which is a legal
 * value the wire deliberately stopped conflating with absence
 * ([#247](https://github.com/Raketa02/Raketa/issues/247)). The caller states which it is
 * sending, exactly as `SearchAsk` does — that decision belongs to the screen that made the
 * comparison, and inferring it from an empty array here would deal a deck against the week a
 * player was trying to leave behind.
 *
 * A deal reached without going through Find a game has no working copy at all, and that is
 * a legal ask rather than a state to guard: the profile's grid is what an omitted override
 * means.
 *
 * ## The prompts ride back, minus the one the deck cannot answer
 *
 * A deal raises them — *"the deal comes back with a `KEEP_THESE_TIMES` prompt, and saving is a
 * separate request the player makes"* — and `SH.saveav`
 * ([#275](https://github.com/Raketa02/Raketa/issues/275)) is the sheet that answers one. It
 * now exists, so the list is carried ([#287](https://github.com/Raketa02/Raketa/issues/287)).
 *
 * **`REFRESH_YOUR_TIMES` is dropped here rather than drawn.** Its *yes* hands the player back
 * to the week grid, and the deck has none — a deal replaces the card in place. Drawing it
 * would either promise a control that is not on the screen or, since dismissal is *not now*
 * and *not now* suppresses it for thirty days, spend the offer on the one surface that cannot
 * honour it. `answerableWithoutAWeekGrid` is where that is decided, over a table of its
 * own so a fifth prompt has to state whether it needs one.
 */

import type { Sport } from '@/shared/vocabulary/sport';
import type { WeekCell } from '@/shared/vocabulary/week';
import { toWireSport } from '@/features/onboarding/types';

import { dealDeck as deal } from '../api/deckApi';
import type { DeckDeal } from '../domain/deckHand';
import type { SearchEnvelope } from '../domain/candidate';
import { answerableWithoutAWeekGrid, type RaisedPrompt } from '../domain/raisedPrompt';
import { toRankedList } from '../mappers/candidateMappers';
import { availabilityOverride, toRaisedPrompts, type PromptQuotes } from '../mappers/searchMappers';

export interface DeckAsk {
  readonly sport: Sport;
  /** The improvised week, or `undefined` to deal on the grid the profile holds. */
  readonly sentWeek: readonly WeekCell[] | undefined;
  /** The two facts a raised prompt's sentence quotes and the response does not carry. */
  readonly quotes: PromptQuotes;
}

/** One deal: the cards, the pool they came from, and the envelope every card is drawn with. */
export interface DeckOutcome extends DeckDeal {
  readonly envelope: SearchEnvelope;
  /**
   * The questions this deal raised, **already filtered to the ones this screen can answer.**
   *
   * The filter is here rather than in the sheet, because it is a fact about the surface and
   * not about the sentence: a component handed a prompt it cannot honour has already been
   * given a question nobody should have asked it.
   */
  readonly prompts: readonly RaisedPrompt[];
}

export async function dealDeck(ask: DeckAsk): Promise<DeckOutcome> {
  const response = await deal({
    sport: toWireSport(ask.sport),
    // The omit-never-null rule is `searchMappers`'; three routes carry the week and #247's
    // distinction has to be drawn identically on all three.
    ...availabilityOverride(ask.sentWeek),
  });

  const { envelope, candidates } = toRankedList(response);
  return {
    envelope,
    candidates,
    pool: envelope.pool,
    prompts: answerableWithoutAWeekGrid(toRaisedPrompts(response, ask.quotes)),
  };
}
