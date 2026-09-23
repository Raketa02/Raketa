/**
 * The deck's two answers — **yes and no, and nothing else.**
 *
 * Both are `features/play/`'s rather than `features/challenges/`': a deck yes is
 * `POST /interest`, a matchmaking write, and the challenge a mutual opens is minted
 * server-side and inline through a port, so neither of these reaches another person directly
 * ([`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md)
 * §8). Left unstated they land in `challenges/`, because *Let's play* sounds like a send.
 *
 * **Both carry the origin key and neither carries a position.** `search_id` says which deal
 * this card came from — *"a yes with no origin is refused rather than recorded with a null
 * link"* — and the backend reads the position off that deal's own rows, so the link is true by
 * construction rather than by a client being honest about where it was scrolled to.
 *
 * ## The yes answers with two facts, and the no answers with none
 *
 * A yes comes back with `mutual` — *"the one thing this tells you about the other person, and
 * you have earned it by them having said yes to you first"* — with **the game the two of them
 * now have**, when there is one to name, and with where the sport stands against its cap,
 * which is the count the segment above the deck draws.
 *
 * A pass answers `204` and **no route anywhere returns one**: not to the passer, not as a
 * count, not as *"you have passed on twelve people"*. So there is nothing to map, and the
 * absence is the contract rather than a shape not yet needed.
 */

import type { Sport } from '@/shared/vocabulary/sport';
import { toWireSport } from '@/features/onboarding/types';

import { expressInterest, recordPass } from '../api/deckApi';
import { toOutstandingAfterTap, type OutstandingInterest } from '../mappers/interestMappers';

/** Which card, and which deal it came off. The same three facts either answer needs. */
export interface CardAnswer {
  readonly sport: Sport;
  readonly playerId: string;
  /** The deal this person was dealt in — the **Origin key**, and required. */
  readonly searchId: string;
}

export interface InterestExpressed {
  /**
   * Whether they had already said it to you.
   *
   * **A mutual is told to both sides and a one-sided yes is told to nobody**, so this is the
   * one bit of the answer that changes what the screen says.
   */
  readonly mutual: boolean;
  /**
   * **The game the two of you have**, when the platform has one to name — the challenge this
   * tap opened, or the one an earlier mutual opened that is not finished with
   * ([ADR-0154](../../../../../docs/adr/0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md)).
   *
   * `null` is **one answer covering two causes** and the screen may not tell them apart: the
   * pair already have a game being *arranged*, or a gate declined to open one. Which it is
   * does not cross the wire and will not, so nothing above this may draw the absence as a
   * state of its own.
   */
  readonly challengeId: string | null;
  /** Where this sport stands after the tap, for the count the segment draws. */
  readonly outstanding: OutstandingInterest;
}

export async function sayYes(answer: CardAnswer): Promise<InterestExpressed> {
  const response = await expressInterest({
    sport: toWireSport(answer.sport),
    player_id: answer.playerId,
    search_id: answer.searchId,
  });

  return {
    mutual: response.mutual,
    challengeId: response.challenge_id,
    outstanding: toOutstandingAfterTap(response.outstanding),
  };
}

export async function sayNo(answer: CardAnswer): Promise<void> {
  await recordPass({
    sport: toWireSport(answer.sport),
    player_id: answer.playerId,
    search_id: answer.searchId,
  });
}
