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
 * **An empty seat is drawn as nothing**, and your own face is the one thing this court marks —
 * see `ringFor` below.
 *
 * **And nothing here announces.** §20.1's rule is *one accessibility element per action, and
 * everything actionless merges into the nearest action above it*. A read-only face has no
 * action; the summary preceding the seats is the element, and it is `Court`'s.
 */

import { Court, courtSeatSize, SeatFace, type CourtFaceOccupant, type SportKey } from '@/shared/ui';

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
        <SeatFace key={at} size={size} occupant={occupant} ring={ringFor(occupant)} />
      ))}
    </Court>
  );
}

/**
 * Which ring, on the court that cannot be touched.
 *
 * **Your own face is ringed in volt**, which is the one accent and is spent here on the one
 * fact this court cannot otherwise state: four faces on a picture of a court, and which of
 * them is you. The interactive court spends volt on the seat you picked for a swap instead —
 * one meaning per surface, because they never appear together
 * ([1.2](../../../../../docs/design-system.md#12-one-accent-used-sparingly)).
 *
 * **An unfilled seat is drawn as nothing at all.** The interactive court's dashed ring is an
 * invitation, and there is nothing to accept here: the court's summary already says how many
 * of the seats are filled, and a ring nobody can press is an affordance that is not one.
 */
function ringFor(occupant: CourtFaceOccupant) {
  switch (occupant.kind) {
    case 'you':
      return 'yours' as const;
    case 'player':
      return 'seated' as const;
    case 'empty':
      return 'none' as const;
  }
}
