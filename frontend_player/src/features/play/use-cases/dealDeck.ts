/**
 * Deal a deck — **one request, and the whole of what the screen asks for.**
 *
 * The deck is the search screen's opposite in every way that matters to a use-case. There is
 * no mode and no declaration (every deal runs under one ruler,
 * [ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §2), no radius (a deal runs on the profile's, and there is no slider to write first), no
 * widening, and **no week**: the deck is reached from a tab of its own, so there is no working
 * copy to have edited, and the deal runs on the profile's grid (ADR-0169 §1). What is left is
 * a sport, which is why this is one request where `findAGame` is two.
 *
 * `availability_override` is therefore never sent — an omitted override *is* the profile's
 * grid ([#247](https://github.com/Raketa02/Raketa/issues/247)), and a deal cannot be asked
 * against any other. It travelled here for as long as the deck was reached from the screen the
 * week is edited on.
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
import { toWireSport } from '@/features/onboarding/types';

import { dealDeck as deal } from '../api/deckApi';
import type { DeckDeal } from '../domain/deckHand';
import type { SearchEnvelope } from '../domain/candidate';
import { answerableWithoutAWeekGrid, type RaisedPrompt } from '../domain/raisedPrompt';
import { toRankedList } from '../mappers/candidateMappers';
import { toRaisedPrompts, type PromptQuotes } from '../mappers/searchMappers';

export interface DeckAsk {
  readonly sport: Sport;
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
  const response = await deal({ sport: toWireSport(ask.sport) });

  const { envelope, candidates } = toRankedList(response);
  return {
    envelope,
    candidates,
    pool: envelope.pool,
    prompts: answerableWithoutAWeekGrid(toRaisedPrompts(response, ask.quotes)),
  };
}
