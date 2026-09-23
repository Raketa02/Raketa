/**
 * The two routes the card is: read the ones still waiting, and answer one.
 *
 * One of the two layers allowed to read generated types, and the only place these paths are
 * written down.
 *
 * ## The read answers ids, and the join is the client's
 *
 * `GET /sportsmanship` carries a `game_id` and everybody else who was on that court, and
 * nothing about who they are. What the people are called, which sport it was and when it
 * happened come from `GET /games` — *"the same join the client already makes to draw the
 * game"* — because repeating them here would be a second copy of an evening's description,
 * and the day the two disagreed the card would name somebody the game did not.
 *
 * ## No `Idempotency-Key`, and the rule is the mechanism
 *
 * The only mutation in this app that carries one is the profile commit, whose key is minted
 * with the draft. A card does not need one: **submitting closes it for ever**, so a duplicate
 * press is made, read and refused by name with `you_have_already_rated_this_game` — the same
 * argument `challengesApi` makes about the pair rule and `gamesApi` makes about a second
 * acceptance. A key beside a rule that does not expire would be the weaker of the two.
 *
 * ## A `signal` on the read and none on the write
 *
 * The asymmetry every api module in this app draws, arriving for the reason and not a
 * different one: a `GET` records nothing, so an abandoned one costs nobody a row, and the
 * `POST` closes a card — a cancelled one can leave the card closed with nobody holding the
 * answer that says so.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type AnswerTheCardRequest = components['schemas']['AnswerTheCardRequest'];
type OpenCardsResponse = components['schemas']['OpenCardsResponse'];

/** The read may be abandoned; the write may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/**
 * **The courts still waiting for your stars, soonest to expire first.**
 *
 * A card appears the day after the game and stays for seven days. A game not yet a day old,
 * one whose week has run out and one already answered are all simply **not here** — *"and
 * none of them is something to draw differently"* — so an empty list is the ordinary answer
 * and the only one.
 */
export function getOpenCards({ signal }: Cancellable = {}): Promise<OpenCardsResponse> {
  return httpRequest<OpenCardsResponse>({
    method: 'GET',
    path: '/api/v1/sportsmanship',
    authenticated: true,
    signal,
  });
}

/**
 * **Everybody from one game, answered together — and it closes the card for ever.**
 *
 * Leaving somebody out of `ratings` leaves them blank, and an empty list answers the card
 * without rating anybody, which is an answer. `204`, and nothing is returned: there is no
 * route through which an individual answer reaches anybody, including the person who gave it.
 */
export function postCardAnswer(gameId: string, body: AnswerTheCardRequest): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `/api/v1/sportsmanship/${gameId}`,
    body,
    authenticated: true,
  });
}
