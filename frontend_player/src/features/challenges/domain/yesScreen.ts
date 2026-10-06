/**
 * **The picture the yes screen draws** — who stands on which side, and who is a face
 * ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §1, §3, §4; [#433](https://github.com/Raketa02/Raketa/issues/433),
 * [#434](https://github.com/Raketa02/Raketa/issues/434)).
 *
 * A route parameter is not app state: the screen reads everything it draws from the challenge
 * the query cache holds, and this file is the two folds over it — one per face of the screen.
 * Two rules, and both are the app's own rather than this screen's:
 *
 * - **The seats are the challenge's, in wire order** — every side-A seat, then every side-B
 *   (`ChallengeDetail.seats`' own contract) — and the reader's side is put first, the reader
 *   first within it. That is `games/domain/pairing.ts`' `sidesForReader` one context over, read
 *   from the reader outward for the same reason: a list of people is read from you.
 * - **A seat is a person only when its occupant has accepted.** Invited and still deciding,
 *   declined, lapsed, left, and nobody at all are one thing — an **empty seat** — because this is
 *   the room's own membership rule (ADR-0146 §7: *a no is not an accepted seat*), and the picture
 *   has to agree with the row the reader lands on next about who is in.
 *
 * `undefined` where the reader holds no accepted seat: a bad or foreign parameter draws nothing
 * and leaves, and a picture of a court the reader is not on would be a picture of somebody
 * else's evening.
 */

import type { YesSeat } from '@/features/proposals/types';

import type { DetailSeat } from './challengeDetail';

export type { YesSeat };

/**
 * The picture in two halves, each in the reader's order — `CourtSides`' shape, one context over.
 *
 * After a challenge's yes the halves are the **court's two sides** (`sidesForReader`); after a
 * mutual's they are **you and them** (`pairForReader`) — the reader alone, and everybody else who
 * has said yes — which is not a court split in two and is deliberately drawn as if it were: the
 * two halves slide in from the two edges and meet, in every sport, with nothing between them.
 */
export interface YesSides {
  /** You first, then whoever else is on your side — or an empty seat. After a mutual, you alone. */
  readonly yours: readonly YesSeat[];
  readonly theirs: readonly YesSeat[];
}

/**
 * Which half of the court a seat is in — every **A**, then every **B** — read off its position,
 * which is the mapper's own arithmetic for a send (`challengeMappers.sideAt`) run the other way.
 */
function sideA(at: number, seats: number): boolean {
  return at < Math.ceil(seats / 2);
}

export function sidesForReader(
  seats: readonly DetailSeat[],
  playerId: string,
): YesSides | undefined {
  const at = seats.findIndex((seat) => seat.playerId === playerId);
  const mine = seats[at];
  if (mine === undefined || mine.answer !== 'ACCEPTED') return undefined;

  const onMySide = (index: number) => sideA(index, seats.length) === sideA(at, seats.length);
  const rest = seats.map(tile);

  return {
    yours: [tile(mine), ...rest.filter((_, index) => index !== at && onMySide(index))],
    theirs: rest.filter((_, index) => !onMySide(index)),
  };
}

function tile(seat: DetailSeat): YesSeat {
  if (seat.playerId === undefined || seat.answer !== 'ACCEPTED') return { kind: 'empty' };

  const photoUrl = seat.card?.person.photoUrl;
  return {
    kind: 'person',
    playerId: seat.playerId,
    ...(seat.name === undefined ? {} : { name: seat.name }),
    ...(photoUrl === undefined ? {} : { photoUrl }),
  };
}

/**
 * **The mutual's picture — you and them, and nobody else** (ADR-0167 §4).
 *
 * The accepted people of the challenge the reply named, the reader first, with no empty seat in
 * it whatever the sport: in tennis the two are opponents on two sides, in padel partners on one
 * side with the other still to fill, and both are true statements about the two people — so the
 * picture says only *you two* and leaves the court's shape to the chat, one tap later. Where
 * `sidesForReader` draws a seat still deciding as an empty seat, this draws nothing for it,
 * because *and here is who has not answered* is a sentence about the court and not about the
 * two of you.
 *
 * **Everybody who has said yes, and not the one this tap was about**: the reply names *the
 * challenge these two have* — the one it minted, or the one an earlier mutual opened that is not
 * finished with (ADR-0154 §1) — and the screen holds the challenge and not the card, so a court
 * that has since grown draws everybody who is in. On the mutual that minted it, that is exactly
 * two.
 *
 * `undefined` for the same reason as the sides': a reader who holds no accepted seat is looking
 * at somebody else's evening.
 */
export function pairForReader(
  seats: readonly DetailSeat[],
  playerId: string,
): YesSides | undefined {
  const mine = seats.find((seat) => seat.playerId === playerId);
  if (mine === undefined || mine.answer !== 'ACCEPTED') return undefined;

  const them = seats
    .filter((seat) => seat.playerId !== playerId && seat.answer === 'ACCEPTED')
    .map(tile);

  return { yours: [tile(mine)], theirs: them };
}

/**
 * How many tiles the picture draws — what sizes them. Counted off the picture and not the court,
 * because a padel mutual is four seats and two faces.
 */
export function tilesIn(sides: YesSides): number {
  return sides.yours.length + sides.theirs.length;
}

/**
 * **The reader's own face, put on their own tile.** The other players' photographs come off the
 * seat cards the challenge carries; nothing carries the reader's own onto a court, so the screen
 * reads it off their own record and hands it in here. The reader is always first in `yours` —
 * `sidesForReader` puts them there, or answers nothing — so this is one seat and never a search.
 * `undefined` leaves the tile as it was: the poster, which is what a reader with no photograph
 * and a read that did not answer both draw.
 */
export function withOwnFace(sides: YesSides, photoUrl: string | undefined): YesSides {
  if (photoUrl === undefined) return sides;
  const [reader, ...partners] = sides.yours;
  if (reader === undefined || reader.kind !== 'person') return sides;
  return { ...sides, yours: [{ ...reader, photoUrl }, ...partners] };
}
