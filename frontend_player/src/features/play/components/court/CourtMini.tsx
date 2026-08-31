/**
 * The **read-only** court — the one on the forecast card and in the pool header.
 *
 * *"`CourtMini` owns nothing but its avatars"*
 * ([`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §4). Every number it draws is `Court`'s: the aspect, the four line-sets, the seat
 * coordinates, the scrim, the caption and the side labels. What is left is who is standing
 * where, and that is this file.
 *
 * **It is a second component and not a flag on the interactive one.** The two share every
 * number and no behaviour, and §3's argument against one card with a `surface` prop is the
 * same argument here: read-only faces and pressable seats are *different children*, and a
 * `interactive` boolean would put `if` at every site that differs.
 *
 * **No labels.** #240 §5: both screens this court appears on already print the handles in
 * full and unavoidably — the forecast card's figures row and the pool header's seated-names
 * line — so a name under a 46pt face would be the third rendering of a word already on screen,
 * cut to four characters. The court's `summary` says how many seats are filled and the screen
 * says who is in them.
 *
 * **And nothing here announces.** §20.1's rule is *one accessibility element per action, and
 * everything actionless merges into the nearest action above it*. A read-only face has no
 * action; the summary preceding the seats is the element, and it is `Court`'s.
 */

import { StyleSheet, View } from 'react-native';

import { Court, courtSeatSize, type SportKey } from '@/shared/ui';

import { CandidatePhoto, candidatePhotoRadius } from '../candidate/CandidatePhoto';

import { seatRing } from './seatRing';

/**
 * Who is in a seat, as a court that cannot be touched needs them: an id, and a link if there
 * is one.
 *
 * Deliberately **less** than `CourtSeat`'s occupant rather than the same type reused — the
 * name, the level and the acceptance are facts the interactive seat draws or decides with, and
 * a caller made to supply them here would be supplying them for nothing. The richer type is
 * structurally one of these, so a screen holding a line-up can hand the same array to both.
 */
export type CourtFaceOccupant =
  | { readonly kind: 'you'; readonly playerId: string }
  | { readonly kind: 'player'; readonly playerId: string; readonly photoUrl?: string }
  | { readonly kind: 'empty' };

export interface CourtMiniProps {
  readonly sport: SportKey;
  readonly width: number;
  /** `courtSummaryLabel`'s sentence. The court places it before the seats; the words are the
   *  screen's, because the pool header and the forecast card do not say the same thing. */
  readonly summary: string;
  readonly caption?: string;
  readonly sideLabels?: readonly [string, string];
  /** In seat order — your side first. The court places them; this file draws them. */
  readonly seats: readonly CourtFaceOccupant[];
}

export function CourtMini({ sport, width, summary, caption, sideLabels, seats }: CourtMiniProps) {
  const size = courtSeatSize(width);

  return (
    <Court sport={sport} width={width} summary={summary} caption={caption} sideLabels={sideLabels}>
      {seats.map((occupant, at) => (
        <Face key={at} size={size} occupant={occupant} />
      ))}
    </Court>
  );
}

/**
 * One face, or the ring where a face is not.
 *
 * The empty seat is the same white ring the seated one wears, **dashed** — the shape that says
 * empty on the interactive court, drawn here without the plus, because there is nothing on
 * this court to press and an add glyph would be an affordance that is not one.
 */
function Face({ size, occupant }: { readonly size: number; readonly occupant: CourtFaceOccupant }) {
  const face = { width: size, height: size, borderRadius: candidatePhotoRadius(size) };

  if (occupant.kind === 'empty') return <View style={[face, seatRing.empty]} />;

  return (
    <View style={face}>
      <CandidatePhoto
        playerId={occupant.playerId}
        photoUrl={occupant.kind === 'you' ? undefined : occupant.photoUrl}
        box={{ kind: 'face', size }}
      />
      <View
        style={[StyleSheet.absoluteFill, { borderRadius: face.borderRadius }, seatRing.seated]}
        pointerEvents="none"
      />
    </View>
  );
}
