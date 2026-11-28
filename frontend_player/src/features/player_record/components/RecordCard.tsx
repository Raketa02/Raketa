/**
 * **The record** — everything anybody has to say about this person, counted or written
 * ([#385](https://github.com/Rakieta02/Rakieta/issues/385),
 * [#660](https://github.com/Rakieta02/Rakieta/issues/660)).
 *
 * Four counts, one printed pair, and what other players said.
 *
 * ## It has no heading, and losing it is what let the rating in
 *
 * The card was headed *counted by the system, not written by people* — a promise about
 * **authorship**, which is why the sportsmanship figure stood outside it in a block of its own.
 * The rating belongs on the record, so the heading went rather than the row: a title claiming
 * nobody wrote any of this, over a star average people wrote, is worse than no title at all.
 *
 * What the heading carried that mattered is now on the row that needs it. *Sportsmanship, by
 * players* names its own author, where every row above it plainly has none.
 *
 * ## Counts, and never a meter
 *
 * Player reliability is points (ADR-0195 §1), and what the record shows beside the figure is four
 * counts over the last 6 months — *Shows up · turned up 12 of 13*, *Keeps plans · kept 13 of 14*,
 * *Being late · late 1 time*, *Results left in dispute · 0*. They replaced the metered strands
 * the old figure was the weighted mean of, and the bars went with them: a bar draws a ratio, and
 * nothing here is one any more. Nothing is tinted either — the tone ladder that painted the bars
 * named a bar at 70 that nothing applies, and the one surface that tints a figure by its band is
 * the Members tag.
 *
 * **The counts are always drawn**, noughts included, because the figure they stand beside is
 * always there: *turned up 0 of 0* is what is true of somebody nothing has fallen due for, and
 * the *New* beside their figure says why.
 *
 * ## The variety row and the rating are their own absences
 *
 * Opponent variety prints `70% · 14 of 20` — the share in words, the pair beside it — and is
 * absent where no counted game was ever recorded. What other players said is absent where nobody
 * has rated them. Neither moves with the other or with the counts.
 *
 * ## One element
 *
 * §20.1: there is no action anywhere on this card, so it is one element and `recordCardLabel` is
 * what it says.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, Row, theme } from '@/shared/ui';

import type { Opinion, OpponentVariety, ReliabilityCounts } from '../domain/playerRecord';

import {
  SPORTSMANSHIP_LABEL,
  VARIETY_LABEL,
  countLines,
  opinionFigure,
  recordCardLabel,
  varietyValue,
} from './recordPresentation';

export interface RecordCardProps {
  /** Player reliability's four counts, over the last 6 months — always there. */
  readonly counts: ReliabilityCounts;
  /** An absence of its own: no counted game has ever been recorded. */
  readonly variety?: OpponentVariety;
  /**
   * What other players said — **an absence asking its own question.**
   *
   * Most people have not been rated, and rating is a favour nothing records the omission of, so
   * this is missing far more often than the rows above it. The figure and its count, for the
   * subject as for a stranger (ADR-0179 §5): the row draws what it was handed and compares
   * nothing, and there is no second arm for it to be handed.
   */
  readonly opinion?: Opinion;
}

export function RecordCard({ counts, variety, opinion }: RecordCardProps) {
  return (
    <Card>
      <View
        accessible
        accessibilityLabel={recordCardLabel({
          counts,
          ...(variety === undefined ? {} : { variety }),
          ...(opinion === undefined ? {} : { opinion }),
        })}
      >
        {countLines(counts).map((line, at) => (
          <Row
            key={line.label}
            label={line.label}
            value={<Text style={s.figure}>{line.value}</Text>}
            divided={at > 0}
          />
        ))}

        {variety === undefined ? null : (
          <Row
            label={VARIETY_LABEL}
            value={<Text style={s.figure}>{varietyValue(variety)}</Text>}
            divided
          />
        )}

        {/* Last, because it is the one row here people wrote and the label says so. It carries
            no tone, like every row on the card: a star average in a band's colours would read as
            a second reliability figure on the screen a player opens to see how they appear. */}
        {opinion === undefined ? null : (
          <Row
            label={SPORTSMANSHIP_LABEL}
            value={<Text style={s.figure}>{opinionFigure(opinion)}</Text>}
            divided
          />
        )}
      </View>
    </Card>
  );
}

const s = StyleSheet.create({
  figure: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
});
