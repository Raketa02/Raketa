/**
 * The face in a seat, and the ring around it — **the drawing both courts share.**
 *
 * [`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md)
 * §4 separates `CourtMini` and `CourtBuild` on behaviour and says in the same breath that they
 * *"share everything that is a number"*. This is that share: the box, its corner, the
 * photo-or-poster switch and the ring over it. What the two do not share is what a seat is
 * *for*, which is why one of them wraps this in a `Pressable` and the other does not.
 *
 * **The ring is drawn over the face rather than as the face's own border**, so selecting a
 * seat does not move the photograph under it in by a point.
 *
 * ## Why it is `shared/ui`
 *
 * It was `features/play/components/court/seatFace`, while Play's courts were the only ones that
 * drew a face. The group page's Friends court and Games card, Fill in's squares and a booked
 * game's players card draw the same face in the same ring, and none of them may import
 * `features/play/` — the loop [#569](https://github.com/Rakieta02/Rakieta/issues/569) removes — so
 * the drawing came below all of them ([#574](https://github.com/Rakieta02/Rakieta/issues/574)), as
 * `PlayerPhoto` under it did. The ring came with it, because the face is its only reader.
 *
 * **Your own seat draws the poster.** `photo_url` is minted for another player's card row;
 * nothing in a line-up carries yours, and `GET /photos/{id}` signs your own by an id this
 * component was never handed. A poster is a fact about an id, so your seat is the one face on
 * a court drawn from an id alone.
 *
 * **And the id is the account's, not the answer's**
 * ([#282](https://github.com/Rakieta02/Rakieta/issues/282)). A builder draws an empty court
 * before anybody has answered for it, so a seat that waited for `Relationship.SELF` to name
 * you sat faceless until a fill came back; the screen reads `GET /users/me` instead and hands
 * the id down, because a drawing may not fetch its own occupant.
 *
 * The field stays **optional** for the one frame that launch read is still in flight, and the
 * answer there is a **seated ring with no face**: a poster invented from a placeholder id
 * would be a picture of somebody else, and a plus would say the seat is open, which the truth
 * table refuses. That is a state rather than a second occupant kind.
 */

import type { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { formatLevel } from '@/shared/formatting/ratingFormat';

import { PlayerPhoto, playerPhotoRadius } from './PlayerPhoto';
import { seatRing, type SeatRing } from './seatRing';
import { theme } from './theme';

/**
 * Who is in a seat, as **a drawing** needs them: an id, and a link if there is one.
 *
 * Deliberately less than `CourtSeat`'s occupant — the name, the level and the acceptance are
 * facts the interactive seat draws or decides with, and neither court needs them to put a face
 * in a box. The richer type is structurally one of these, so a screen holding a line-up hands
 * the same array to both courts.
 */
export type CourtFaceOccupant =
  | { readonly kind: 'you'; readonly playerId?: string }
  | { readonly kind: 'player'; readonly playerId: string; readonly photoUrl?: string }
  | { readonly kind: 'empty' };

/** The box, and its corner — `PlayerPhoto`'s share of its own width, at one owner. */
export function seatBox(size: number) {
  return { width: size, height: size, borderRadius: playerPhotoRadius(size) };
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
   *  court puts nothing, because there is nothing on it to press. It is drawn only for a seat
   *  that is genuinely empty — a faceless *you* is not one, and a plus there would say so. */
  readonly children?: ReactNode;
}

export function SeatFace({ size, occupant, ring, children }: SeatFaceProps) {
  const box = seatBox(size);
  // Two seats draw no face and only one of them is empty — see the module note. `children` is
  // the empty seat's own plus, so it is drawn where there is a seat to fill and nowhere else.
  const face = occupant.kind === 'empty' ? undefined : occupant.playerId;

  return (
    <View style={[box, face === undefined ? s.empty : undefined]}>
      {face === undefined ? (
        children
      ) : (
        <PlayerPhoto
          playerId={face}
          photoUrl={occupant.kind === 'player' ? occupant.photoUrl : undefined}
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

// ---------------------------------------------------------------------------
// The identifier under the face
// ---------------------------------------------------------------------------

/**
 * How much of a handle a seat draws — **three characters, and the whole of the rule.**
 *
 * Exported so the test that pins it is testing the rule rather than a slice written twice.
 */
export const SEAT_NAME_LETTERS = 3;

/** The drawn identifier: the handle's first three characters, and never a mark for the rest. */
export function seatCaptionName(name: string): string {
  return name.slice(0, SEAT_NAME_LETTERS);
}

export interface SeatCaptionProps {
  /** The seat's face size. The caption hangs `space.xxs` below it. */
  readonly size: number;
  /** The **whole** handle. It is cut here and never by the caller — see the module note. */
  readonly name: string;
  /**
   * The Skill level, where the record still holds one.
   *
   * Absent on an empty seat, on a withheld one whose card is gone with its handle, and on a
   * **game's** seat, which carries a handle and nothing else about the person in it
   * ([ADR-0141](../../../../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)).
   */
  readonly level?: number;
}

/**
 * **The identifier under a face, and it is three letters** — 7.12's caption, drawn by all three
 * courts that have one.
 *
 * It moved here from `CourtSeat` when Now's card drew the third court
 * ([#367](https://github.com/Rakieta02/Rakieta/issues/367)). The rule and the geometry travel
 * together on purpose: the three-character cut was already exported so a test could pin it, and
 * the negative insets, the `tag` role and the media shadow are the half a second copy would have
 * drifted on first.
 *
 * Sixty-four characters of handle in a 60pt seat is about five, so the visible label is not the
 * name and cannot be: it draws the first three, **hard, with no ellipsis**, because an ellipsis
 * spends one of four characters saying *there was more* on a caption whose whole job is telling
 * four faces apart. **The sentence and the spoken name stay whole** — a truncation of a drawing
 * invents nothing, which is the only thing
 * [ADR-0107](../../../../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md)
 * forbids.
 *
 * **Hidden**, always: the seat around it already carries the whole handle and the level in its
 * own name, so this is the same word cut short and the same figure.
 */
export function SeatCaption({ size, name, level }: SeatCaptionProps) {
  return (
    <View
      style={[c.caption, { top: size + theme.space.xxs }]}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {/* `clip` rather than `tail`: the cut is already made, so an ellipsis here could only
          appear where a three-character word somehow overran, and it would be a mark nobody
          could act on. `numberOfLines` stays, because Dynamic Type can still overrun. */}
      <Text style={c.label} numberOfLines={1} ellipsizeMode="clip">
        {seatCaptionName(name)}
      </Text>
      {level === undefined ? null : (
        <Text style={c.level} numberOfLines={1}>
          {formatLevel(level)}
        </Text>
      )}
    </View>
  );
}

const c = StyleSheet.create({
  // Wider than the face it sits under, because the name and the level share its one line —
  // absolutely positioned, so the negative insets take room from nothing.
  caption: {
    position: 'absolute',
    left: -theme.space.sm,
    right: -theme.space.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.space.xxs,
  },
  label: {
    ...theme.type.tag,
    ...theme.shadow.textOnMedia,
    color: theme.color.surface,
    textAlign: 'center',
  },
  // Mono and tabular, because four of these are read down a court against each other — 1.4's
  // whole reason for mono, and the comparison the side strengths above cannot answer.
  level: {
    ...theme.num.xs,
    ...theme.tabular,
    ...theme.shadow.textOnMedia,
    color: theme.color.surface,
    textAlign: 'center',
  },
});
