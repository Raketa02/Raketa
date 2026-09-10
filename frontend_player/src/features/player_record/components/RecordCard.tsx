/**
 * **The record** — everything anybody has to say about this person, counted or written
 * ([#385](https://github.com/Raketa02/Raketa/issues/385)).
 *
 * Three metered rows, one printed pair, and what other players said.
 *
 * ## It has no heading, and losing it is what let the rating in
 *
 * The card was headed *counted by the system, not written by people* — a promise about
 * **authorship**, which is why the sportsmanship figure stood outside it in a block of its own
 * and why `countedRows` still drops the strand of that name. The rating belongs on the record,
 * so the heading went rather than the row: a title claiming nobody wrote any of this, over a
 * star average people wrote, is worse than no title at all.
 *
 * What the heading carried that mattered is now on the row that needs it. *Sportsmanship, by
 * players* names its own author, where every row above it plainly has none — and the sentence
 * under the card says the thing the label cannot, which is that a low one acts on nobody.
 *
 * ## The card is the pill's account, and the pill is the matcher's own number
 *
 * The figure in the header is the weighted mean of the figures here. That is the whole reason
 * this screen is worth having: **a penalty nobody can look up is a penalty nobody can fix**, so
 * somebody held back by their Player Score can read the rows behind it and watch the number
 * lift. Which is also why nothing here is recomputed — the rows and the figure are the
 * platform's, and a client that blended them would be a second opinion about a penalty.
 *
 * ## Nothing is ever a nought, and an absence is not drawn
 *
 * A strand nobody can measure and a strand nothing has fallen due under for *them* are the same
 * absence, and neither is a zero: *we have not seen enough* and *they are bad at this* are
 * different facts. So a card with one row draws one row, and a card with nothing to draw is not
 * drawn at all — there is no empty state, no *no record yet*, and no panel of noughts for a
 * newcomer to be mistaken for a bad record.
 *
 * ## The variety row carries no bar, and that is a decision
 *
 * The contract publishes two counts and attaches no banding, floor or tone to the share. An
 * untoned meter in a column of toned ones would make a tone claim by adjacency, so the row
 * prints `70% · 14 of 20` and draws nothing — the percentage is in words precisely because
 * there is no bar to read it off.
 *
 * ## One element, and the bars are inside it
 *
 * §20.1: there is no action anywhere on this sheet, so the card is one element and
 * `recordCardLabel` is what it says. Every meter in it is hidden and takes no name, because the
 * fraction it draws is spoken two words earlier.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, Row, theme } from '@/shared/ui';

import type { Opinion, OpponentVariety, Reliability } from '../domain/playerRecord';
import { countedRows } from '../domain/recordCard';

import { StrandMeterRow } from './StrandMeterRow';
import {
  SPORTSMANSHIP_LABEL,
  VARIETY_LABEL,
  opinionValue,
  recordCardLabel,
  varietyValue,
} from './recordPresentation';

export interface RecordCardProps {
  /** Absent where nothing has ever fallen due for them. */
  readonly reliability?: Reliability;
  /** A different absence: no counted game has ever been recorded. */
  readonly variety?: OpponentVariety;
  /**
   * What other players said — **a third absence, asking a third question.**
   *
   * Most people have not been rated, and rating is a favour nothing records the omission of, so
   * this is missing far more often than the rows above it. Which arm it is — a figure for a
   * reader, a band for the subject — is folded at the wire boundary from `is_self`, so the row
   * draws what it was handed and compares nothing.
   */
  readonly opinion?: Opinion;
}

export function RecordCard({ reliability, variety, opinion }: RecordCardProps) {
  const rows = reliability === undefined ? [] : countedRows(reliability.strands);
  const drawn = rows.length > 0;

  // Nothing to say is said by not being here — the same spelling every absence takes on this
  // sheet, and the one that keeps a newcomer's record reading as new rather than as poor.
  if (!drawn && variety === undefined && opinion === undefined) return null;

  return (
    <Card>
      <View
        accessible
        accessibilityLabel={recordCardLabel({
          rows,
          ...(variety === undefined ? {} : { variety }),
          ...(opinion === undefined ? {} : { opinion }),
        })}
      >
        {rows.map((row, at) => (
          <StrandMeterRow key={row.strand} row={row} divided={at > 0} />
        ))}

        {variety === undefined ? null : (
          <Row
            label={VARIETY_LABEL}
            value={<Text style={s.figure}>{varietyValue(variety)}</Text>}
            divided={drawn}
          />
        )}

        {/* Last, because it is the one row here people wrote and the label says so. It carries
            no bar for the variety row's reason and no tone for its own: `scoreTone` belongs to
            the Player Score, and a three-step band in those three colours would read as a
            second score on the screen a held player opens to find out what holds them back. */}
        {opinion === undefined ? null : (
          <Row
            label={SPORTSMANSHIP_LABEL}
            value={<Text style={s.figure}>{opinionValue(opinion)}</Text>}
            divided={drawn || variety !== undefined}
          />
        )}
      </View>
    </Card>
  );
}

const s = StyleSheet.create({
  figure: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
});
