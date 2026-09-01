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
 * ## What this deliberately does not carry back
 *
 * **The prompts.** A deal raises them — *"the deal comes back with a `KEEP_THESE_TIMES`
 * prompt, and saving is a separate request the player makes"* — and `SH.saveav`
 * ([#275](https://github.com/Raketa02/Raketa/issues/275)) is the surface that answers one.
 * Carrying a second list nothing reads would be a DTO with fields nobody checks, and it would
 * be re-shaped by the ticket that gives both surfaces their reader anyway.
 */

import type { Sport } from '@/shared/vocabulary/sport';
import type { WeekCell } from '@/shared/vocabulary/week';
import { toWireSport } from '@/features/onboarding/types';

import { dealDeck as deal } from '../api/deckApi';
import type { DeckDeal } from '../domain/deckHand';
import type { SearchEnvelope } from '../domain/candidate';
import { toRankedList } from '../mappers/candidateMappers';
import { availabilityOverride } from '../mappers/searchMappers';

export interface DeckAsk {
  readonly sport: Sport;
  /** The improvised week, or `undefined` to deal on the grid the profile holds. */
  readonly sentWeek: readonly WeekCell[] | undefined;
}

/** One deal: the cards, the pool they came from, and the envelope every card is drawn with. */
export interface DeckOutcome extends DeckDeal {
  readonly envelope: SearchEnvelope;
}

export async function dealDeck(ask: DeckAsk): Promise<DeckOutcome> {
  const response = await deal({
    sport: toWireSport(ask.sport),
    // The omit-never-null rule is `searchMappers`'; three routes carry the week and #247's
    // distinction has to be drawn identically on all three.
    ...availabilityOverride(ask.sentWeek),
  });

  const { envelope, candidates } = toRankedList(response);
  return { envelope, candidates, pool: envelope.pool };
}
