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
 * The cards that can be drawn, **in the order they were served** — soonest to expire first.
 *
 * A card whose game is not on the list is dropped rather than drawn with ids in it. That is a
 * real state and not a defensive one: a game whose sport or whose court this build cannot read
 * is refused whole by the games mapper, and a card over it would have nobody to name.
 */
export function cardsOnCourts(
  cards: readonly OpenCard[],
  courts: readonly RatedCourt[],
): readonly CardOnACourt[] {
  return cards.flatMap((card) => {
    const court = courts.find((one) => one.gameId === card.gameId);
    if (court === undefined) return [];

    return [{ card, court, subjects: card.players.map((playerId) => named(playerId, court)) }];
  });
}

function named(playerId: string, court: RatedCourt): StarSubject {
  const nickname = court.seats.find((seat) => seat.playerId === playerId)?.nickname;

  return {
    playerId,
    name: nickname === undefined ? { kind: 'unknown' } : { kind: 'player', nickname },
  };
}
