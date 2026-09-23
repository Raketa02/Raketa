/**
 * **One metered row** — what the platform watched, the raw pair it watched it over, and a bar
 * that adds no fact ([#385](https://github.com/Raketa02/Raketa/issues/385)).
 *
 * `Shows up` on the left, `9 of 9` on the right, the meter beneath both. It is the why-fit
 * row's shape one sheet over, which is not a coincidence: both are a fact stated in words with
 * a drawing of the same number under it, and that is the arrangement
 * [7.3](../../../../docs/design-system.md#73-meter-and-bar)'s meter exists for.
 *
 * ## The pair is printed because the bar cannot say it
 *
 * A perfect record over nine games and one over forty draw the **same bar**. That is the whole
 * argument for the row carrying three numbers and drawing two of them, and it is the argument
 * the variety row beneath the card inherits.
 *
 * ## The bar draws the served figure and never a second division
 *
 * `pct` is the platform's own rounding of `good` over `opportunities`, halves up. Dividing here
 * instead would be a fourth rounding of one record, and the two disagree by a point on exactly
 * the values a player looks at twice.
 *
 * ## The tone is the pill's rule, read a second time rather than written a second time
 *
 * `scoreTone` is what tints the reliability pill in the header. One ladder, so a bar and the
 * pill above it can never disagree about the same ratio — which is the defect a threshold
 * written twice eventually produces, silently, on the one screen built to be looked at.
 *
 * ## It announces nothing of its own
 *
 * The card is one accessibility element and states every row in its own label (§20.1); the
 * meter is hidden and takes no name at all, because the fraction is text two words earlier.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Meter, Row, theme } from '@/shared/ui';

import type { StrandRow } from '../domain/playerRecord';
import { scoreTone } from '../domain/scoreTone';

import { STRAND_NAME, strandFraction } from './recordPresentation';

/** `pct` is served as a whole percentage; a meter's share is 0 to 1. */
const PERCENT_SCALE = 100;

export interface StrandMeterRowProps {
  readonly row: StrandRow;
  /** 5.5's `index > 0`. The first row under the heading is undivided. */
  readonly divided?: boolean;
}

export function StrandMeterRow({ row, divided = false }: StrandMeterRowProps) {
  return (
    <View style={s.row}>
      <Row
        label={STRAND_NAME[row.strand]}
        value={<Text style={s.figure}>{strandFraction(row)}</Text>}
        divided={divided}
      />
      <Meter share={row.pct / PERCENT_SCALE} tone={scoreTone(row.pct)} />
    </View>
  );
}

const s = StyleSheet.create({
  // The meter sits under the row rather than in it, so the bar spans the card's whole width
  // and the three of them read as one column.
  row: { gap: theme.space.xxs },
  figure: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
});
