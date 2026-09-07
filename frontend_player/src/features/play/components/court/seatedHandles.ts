/**
 * Who is standing on one half of the court, and what each of them is called.
 *
 * **Two callers, which is what this module was extracted for.** `BuilderScreen`'s forecast card
 * labels a strength with it and offers each name as the way into `SH.whyfit`; `PoolHeader` names
 * the same two halves off the same seating, in the split row and on the balance bar's own
 * segments ([#298](https://github.com/Raketa02/Raketa/issues/298),
 * [#299](https://github.com/Raketa02/Raketa/issues/299)). Two readings of one seating would be
 * two chances for the row saying *You + Marek is worth 2,82* and the row saying who is on your
 * side to disagree about who is standing where — which is the argument written above `halfOf`
 * about two readings inside one screen, and it holds harder across two.
 *
 * **It lives in `components/court/` rather than in `domain/`**, beside `seatWho.ts`, which is
 * the same question asked for the interactive seat. What it reads — a `Candidate` row, a
 * `photoUrl` — are facts a **drawing** needs, and
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §7 puts a rule somebody could be wrong about in `domain/` and everything else beside the
 * thing that draws it.
 *
 * **`place` and `candidate` are the forecast card's**, and a caller that reads neither is not a
 * reason to narrow the type: `place` is what lets a name open with the same two words the
 * seat's own spoken name does, and `candidate` is what makes a name a control rather than a
 * button that opens an apology.
 *
 * **Which half a seat is on is asked and never decided here** (`courtHalfOf`). The function
 * arrived from `BuilderScreen` still drawing that line itself, as
 * `mine !== (place !== 'THEIR_SIDE')`, while `lineup.ts` had already claimed the ground in
 * writing — *"somebody can be very wrong about which half is yours"*
 * ([#300](https://github.com/Raketa02/Raketa/issues/300)).
 */

import { playerName, type NamedPlayer } from '@/shared/formatting/playerName';

import type { Candidate } from '../../domain/candidate';
import type { Seating } from '../../domain/forecast';
import { courtHalfOf, type CourtHalf, type SeatPlace } from '../../domain/lineup';

/**
 * One printed handle, with **the two things that decide whether it is a control**.
 *
 * The place, because the button opens with the same two words the seat's own spoken name does
 * and `seatedNameLabel` composes from the code rather than from the heading the row draws. And
 * the row behind it, because that is both the test — *is there a breakdown to open* — and the
 * whole of what `SH.whyfit` is handed.
 */
export interface SeatedHandle {
  readonly place: SeatPlace;
  /** §15's whole handle, or the unknown's question mark. Never cut short here. */
  readonly name: string;
  /**
   * Whose face to draw beside the handle — **the same photo-or-poster switch the seat takes**.
   *
   * `undefined` for exactly one seat: yours, for the frame the launch read is still in flight
   * (`self` is the account's id and arrives with it). A withheld player keeps a face, because a
   * poster is a fact about an **id** and the id is the one field a withheld row still carries.
   */
  readonly face?: { readonly playerId: string; readonly photoUrl?: string };
  /**
   * The row the record still holds for them. **Absent is plain text**: you have no candidate
   * row because no route serves a searcher their own, and a withheld player has one field and
   * no card — so there is nothing behind the name and it is not a button. A name is a control
   * where there is something behind it and plain text where there is not, never a button that
   * opens an apology.
   */
  readonly candidate?: Candidate;
}

/**
 * The handles on one half of the court, **whole**.
 *
 * §15's `playerName()` is the one formatter, and this returns a **list**: *"a formatter that
 * returns one string has decided the layout, and this one must not"* — at 64 characters a join
 * produces a phrase no row can hold. A seat the record can no longer describe answers the
 * unknown's question mark, which is the same word the seat itself draws.
 */
export function handlesOn(
  half: CourtHalf,
  seated: Seating,
  places: readonly SeatPlace[],
  court: { readonly rows: ReadonlyMap<string, Candidate>; readonly self: string | undefined },
): readonly SeatedHandle[] {
  return seated.flatMap<SeatedHandle>((seat, at) => {
    const place = places[at];
    if (place === undefined || courtHalfOf(place) !== half) return [];
    if (seat.kind === 'you') {
      // No `photoUrl`: no route serves a searcher their own card, so your own face here is the
      // poster your seat already draws — one id, one poster, on both surfaces.
      const face = court.self === undefined ? {} : { face: { playerId: court.self } };
      return [{ place, name: playerName({ kind: 'you' }), ...face }];
    }
    if (seat.kind === 'empty') return [];

    const row = court.rows.get(seat.playerId);
    const who: NamedPlayer =
      row === undefined ? { kind: 'unknown' } : { kind: 'player', nickname: row.card.nickname };
    const photo = row?.card.photoUrl;

    return [
      {
        place,
        name: playerName(who),
        face: { playerId: seat.playerId, ...(photo === undefined ? {} : { photoUrl: photo }) },
        ...(row === undefined ? {} : { candidate: row }),
      },
    ];
  });
}
