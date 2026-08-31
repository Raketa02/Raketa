/**
 * The face in a seat, and the ring around it — **the drawing both courts share.**
 *
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §4 separates `CourtMini` and `CourtBuild` on behaviour and says in the same breath that they
 * *"share everything that is a number"*. This is that share: the box, its corner, the
 * photo-or-poster switch and the ring over it. What the two do not share is what a seat is
 * *for*, which is why one of them wraps this in a `Pressable` and the other does not.
 *
 * **The ring is drawn over the face rather than as the face's own border**, so selecting a
 * seat does not move the photograph under it in by a point.
 *
 * **Your own seat draws the poster.** `photo_url` is minted for another player's card row;
 * nothing in a line-up carries yours, and `GET /photos/{id}` signs your own by an id this
 * component was never handed. A poster is a fact about an id, so your seat is the one face on
 * a court drawn from an id alone.
 */

import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { CandidatePhoto, candidatePhotoRadius } from '../candidate/CandidatePhoto';

import { seatRing, type SeatRing } from './seatRing';

/**
 * Who is in a seat, as **a drawing** needs them: an id, and a link if there is one.
 *
 * Deliberately less than `CourtSeat`'s occupant — the name, the level and the acceptance are
 * facts the interactive seat draws or decides with, and neither court needs them to put a face
 * in a box. The richer type is structurally one of these, so a screen holding a line-up hands
 * the same array to both courts.
 */
export type CourtFaceOccupant =
  | { readonly kind: 'you'; readonly playerId: string }
  | { readonly kind: 'player'; readonly playerId: string; readonly photoUrl?: string }
  | { readonly kind: 'empty' };

/** The box, and its corner — `CandidatePhoto`'s share of its own width, at one owner. */
export function seatBox(size: number) {
  return { width: size, height: size, borderRadius: candidatePhotoRadius(size) };
}

export interface SeatFaceProps {
  /** Decided by the court from its own width. Neither the face nor the seat picks it. */
  readonly size: number;
  readonly occupant: CourtFaceOccupant;
  /**
   * Which ring, decided by the **court** rather than read off the occupant.
   *
   * The two courts do not read the same facts off one person: an empty seat is a target on the
   * interactive court and a gap on the read-only one, and only the read-only court has an
   * accent left to spend on saying which seat is yours.
   */
  readonly ring: SeatRing;
  /** What stands in an **empty** seat. The interactive court puts a plus here; the other
   *  court puts nothing, because there is nothing on it to press. */
  readonly children?: ReactNode;
}

export function SeatFace({ size, occupant, ring, children }: SeatFaceProps) {
  const box = seatBox(size);
  const empty = occupant.kind === 'empty';

  return (
    <View style={[box, empty ? s.empty : undefined]}>
      {empty ? (
        children
      ) : (
        <CandidatePhoto
          playerId={occupant.playerId}
          photoUrl={occupant.kind === 'you' ? undefined : occupant.photoUrl}
          box={{ kind: 'face', size }}
        />
      )}

      <View
        style={[StyleSheet.absoluteFill, { borderRadius: box.borderRadius }, seatRing[ring]]}
        pointerEvents="none"
      />
    </View>
  );
}

const s = StyleSheet.create({
  // Only the empty seat centres anything: a face fills its box, and a plus stands in one.
  empty: { alignItems: 'center', justifyContent: 'center' },
});
