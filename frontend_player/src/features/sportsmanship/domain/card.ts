/**
 * **One court still waiting for this player's stars**, and the game that gives it words.
 *
 * `GET /sportsmanship` answers *ids and nothing else* — a `game_id` and everybody else who was
 * on that court, in the line-up's own order. What the people are called and which sport it was
 * come from the games list the card is drawn beside, joined on `game_id`, *"because repeating
 * them here would be a second copy of an evening's description, and the day the two disagreed
 * the card would name somebody the game did not."*
 *
 * ## The court is handed down, and this feature declares the shape of it
 *
 * {@link RatedCourt} is what a card needs to know about an evening and nothing else. It is
 * declared here rather than imported from `games` for the reason the record sheet gives about
 * its own props: a component that reads no global state is one three surfaces can share, and a
 * feature that named another feature's entity in its own signature would have taken that
 * feature's whole shape as its contract. `games` satisfies it structurally, which is the seam
 * `play` already has with the challenge send — **the surface composes, the feature owns the
 * act.**
 *
 * ## One evening, because the card is asked where the evening is read
 *
 * The card used to be drawn over the whole games list, so the join took a list of cards against
 * a list of courts and kept whatever matched. It is asked at the end of the **result screen**
 * now — the screen is about one game, so the join is about one game, and what it answers is a
 * card or nothing. The list read behind it is unchanged: `GET /sportsmanship` still answers
 * every court still waiting, and this picks the one the screen is on rather than asking the
 * server a question it has no route for.
 *
 * ## The window is the server's, and it is never re-derived here
 *
 * A card appears the day after the game and stays for seven days; a game already answered, one
 * not yet a day old and one whose week has run out are all simply **not on the list**. So this
 * file draws exactly what it was served and computes no eligibility of its own — a second
 * spelling of that window on the client is one that would eventually disagree with the one the
 * `POST` is judged against, and it would disagree silently.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';
import type { Sport } from '@/shared/vocabulary/sport';

/** One card, as the wire answers it: a game, and everybody else who was on that court. */
export interface OpenCard {
  readonly gameId: string;
  /**
   * Everybody else on the court, in the line-up's own order — in doubles both opponents **and**
   * your partner, in singles the one opponent. Never the reader: you rate everybody else on the
   * court and nobody else, so there is no seat of your own to skip.
   */
  readonly players: readonly string[];
}

/** One person on the court, as much of them as a card needs. */
export interface RatedSeat {
  readonly playerId: string;
  /** Absent where `users` no longer has that account, which draws the unknown player's `?`. */
  readonly nickname?: string;
}

/** The evening a card is about, handed down by whoever holds the games. See the module note. */
export interface RatedCourt {
  readonly gameId: string;
  readonly sport: Sport;
  readonly seats: readonly RatedSeat[];
}

/** Somebody the card asks about, named through the seat they held. */
export interface StarSubject {
  readonly playerId: string;
  /**
   * The **whole** handle or nobody
   * ([ADR-0107](../../../../../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md) §4).
   * `unknown` is a seat with no handle left, which is a person who can still be rated.
   */
  readonly name: NamedPlayer;
}

/** A card, the evening behind it, and the people it names. */
export interface CardOnACourt {
  readonly card: OpenCard;
  readonly court: RatedCourt;
  readonly subjects: readonly StarSubject[];
}

/**
 * This court's card, or nothing — which is the ordinary answer.
 *
 * **Nothing** covers all four absences, and they are one thing to a reader: the game is not a
 * day old yet, its week has run out, it was answered already, or the result has not settled.
 * Every one of them is *not on the server's list*, and none of them is re-derived here — a
 * second spelling of that window on this side is one that would eventually disagree with the
 * one the `POST` is judged against, and it would disagree silently.
 */
export function cardOnCourt(
  cards: readonly OpenCard[],
  court: RatedCourt,
): CardOnACourt | undefined {
  const card = cards.find((one) => one.gameId === court.gameId);
  if (card === undefined) return undefined;

  return { card, court, subjects: card.players.map((playerId) => named(playerId, court)) };
}

function named(playerId: string, court: RatedCourt): StarSubject {
  const nickname = court.seats.find((seat) => seat.playerId === playerId)?.nickname;

  return {
    playerId,
    name: nickname === undefined ? { kind: 'unknown' } : { kind: 'player', nickname },
  };
}
