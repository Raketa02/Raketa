/**
 * **The picture the yes screen draws** — who stands on which side, and who is a face
 * ([ADR-0166](../../../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §1, §3; [#433](https://github.com/Raketa02/Raketa/issues/433)).
 *
 * A route parameter is not app state: the screen reads everything it draws from the challenge
 * the query cache holds, and this file is the fold over it. Two rules, and both are the app's
 * own rather than this screen's:
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

import type { DetailSeat } from './challengeDetail';

/** One tile: somebody who has said yes, with the photograph the seat card carries — or nobody. */
export type YesSeat =
  | {
      readonly kind: 'person';
      readonly playerId: string;
      /** The whole handle, for the spoken sentence. Absent where `users` has lost the account. */
      readonly nickname?: string;
      /** Off the seat card; absent for the reader, whose face comes off their own record. */
      readonly photoUrl?: string;
    }
  | { readonly kind: 'empty' };

/** The court split in two, each half in the reader's order — `CourtSides`' shape, one context over. */
export interface YesSides {
  /** You first, then whoever else is on your side — or an empty seat. */
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
    ...(seat.nickname === undefined ? {} : { nickname: seat.nickname }),
    ...(photoUrl === undefined ? {} : { photoUrl }),
  };
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
