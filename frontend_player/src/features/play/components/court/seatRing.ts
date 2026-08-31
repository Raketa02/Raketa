/**
 * The ring around a face on a court — **the one number the two courts share that the design
 * system is not entitled to.**
 *
 * [7.12](../../../../../docs/design-system.md#712-the-court) puts it here in writing: *"the
 * seat face is a share of the court with a floor… Its **radius and its ring are not here**:
 * the court owns where a seat goes and how big its box is, and the seat owns what is drawn in
 * it."* So it cannot be a `theme.size.court` token. And
 * [`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §4 says the read-only court and the interactive one *"share everything that is a number"*,
 * so it cannot be two copies either — `CourtMini` draws the same ring `CourtSeat` does, and
 * two literals is how one of them ends up at 1,5 the day somebody adjusts a screen.
 *
 * One file, two consumers, and the rule that decided both:
 *
 * ```
 * seated     surface, 2        the face is a photograph and the ring is what separates it
 *                              from a generated ground the same white is drawn over
 * empty      surface, 2, DASHED
 * selected   volt, 3           a stroke, on the one kind of bed volt may be one
 * ```
 *
 * **The empty seat differs by a shape and not by a second white.** Part 13's *never colour as
 * the only signal* reads on the sighted half too, and a dimmer white would be a value nobody
 * could name — `Tick.tsx` settled the same question one folder up with three shapes rather
 * than three colours.
 *
 * **The ring is drawn over the face rather than as the face's own border**, at both call
 * sites, so selecting a seat does not move the photograph under it in by a point.
 */

import { StyleSheet } from 'react-native';

import { theme } from '@/shared/ui';

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
});
