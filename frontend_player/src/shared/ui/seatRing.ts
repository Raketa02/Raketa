/**
 * The ring around a face on a court — **the one number the two courts share that the design
 * system is not entitled to.**
 *
 * [7.12](../../../docs/design-system.md#712-the-court) puts it here in writing: *"the
 * seat face is a share of the court with a floor… Its **radius and its ring are not here**:
 * the court owns where a seat goes and how big its box is, and the seat owns what is drawn in
 * it."* So it cannot be a `theme.size.court` token. And
 * [`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md)
 * §4 says the read-only court and the interactive one *"share everything that is a number"*,
 * so it cannot be two copies either — `CourtMini` draws the same ring `CourtSeat` does, and
 * two literals is how one of them ends up at 1,5 the day somebody adjusts a screen.
 *
 * One file, four values, and the rule that decided each:
 *
 * ```
 * seated     surface, 2         the face is a photograph, and the ring is what separates it
 *                               from a generated ground the same white is drawn over
 * empty      surface, 2, DASHED the interactive court's open seat — and the game card's, for a
 *                               seat somebody left (ADR-0162), with no plus in it
 * selected   volt, 3            picked for a swap
 * yours      volt, 2            which seat is you, on the READ-ONLY court
 * none       -                  the read-only court's absent player, who is not drawn at all
 * ```
 *
 * **The empty seat differs by a shape and not by a second white.** Part 13's *never colour as
 * the only signal* reads on the sighted half too, and a dimmer white would be a value nobody
 * could name — `Tick.tsx`, beside it, settled the same question with three shapes rather
 * than three colours.
 *
 * **Volt means two things and they never share a court.** On `CourtBuild` it is the seat you
 * picked for a swap; on `CourtMini` it is which seat is you. The read-only court has no
 * selection to confuse it with and the interactive one marks nobody, so the accent carries one
 * meaning per surface — which is what [1.2](../../../docs/design-system.md#12-one-accent-used-sparingly)
 * asks and what makes two components cheaper than one with a flag.
 *
 * **The ring is drawn over the face rather than as the face's own border**, at both call
 * sites, so selecting a seat does not move the photograph under it in by a point.
 */

import { StyleSheet } from 'react-native';

import { theme } from './theme';

/** Two points of white, three of volt. The seat's own numbers, on `THUMB`'s precedent. */
const RING = { width: 2, selected: 3 } as const;

export const seatRing = StyleSheet.create({
  seated: { borderWidth: RING.width, borderColor: theme.color.surface },
  empty: {
    borderWidth: RING.width,
    borderColor: theme.color.surface,
    borderStyle: 'dashed',
  },
  // Volt as a STROKE, which is legal only on dark — and a court's ground is `night` under
  // `courtScrim` whatever the Sport, which is the whole reason 2.5 has four rows rather than
  // four per screen.
  selected: { borderWidth: RING.selected, borderColor: theme.color.volt },
  yours: { borderWidth: RING.width, borderColor: theme.color.volt },
  // A seat nobody is in, on a court nobody can press. The read-only court draws no ring and no
  // face for an absent player — there is nothing to invite and nothing to state, and the
  // court's summary already says how many seats are filled.
  none: {},
});

/** Which of the five a seat is wearing. The **caller** decides, because the two courts do not
 *  read the same facts off one occupant: an empty seat is a target on one and a gap on the
 *  other, and only the read-only court has an accent to spend on saying which seat is yours. */
export type SeatRing = keyof typeof seatRing;
