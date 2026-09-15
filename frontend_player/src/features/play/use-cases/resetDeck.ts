/**
 * *Show them again* — deal the deck whole again, for one sport.
 *
 * It lifts, for that sport only, every pass suppression, the day's dealt memory and the
 * cool-off ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §5). The durable record of each pass stays — a re-shown card is still a re-show — and live
 * outgoing yeses are not touched: the people already said yes to are still theirs to wait on.
 *
 * **It answers nothing**, by contract: the next deal is where the difference shows. So the
 * use-case is the write and no more, and the screen that presses it deals again afterwards —
 * the held deal replaced rather than appended to, because a reset re-deals people the held deal
 * has already recorded as answered.
 */

import type { Sport } from '@/shared/vocabulary/sport';
import { toWireSport } from '@/features/onboarding/types';

import { resetDeck as reset } from '../api/deckApi';

export async function resetDeck(sport: Sport): Promise<void> {
  await reset({ sport: toWireSport(sport) });
}
