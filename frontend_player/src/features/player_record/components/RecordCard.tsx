/**
 * **The record** — everything the platform has watched this person do, under the rule it
 * enforces ([#385](https://github.com/Raketa02/Raketa/issues/385)).
 *
 * Three metered rows and one printed pair. The heading is *counted by the system, not written
 * by people*, and it is a promise about **authorship** rather than a title: what other players
 * said stands one block down under a heading naming its own author, and the row that would
 * break this one is dropped in `countedRows` rather than trusted not to arrive.
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

import type { OpponentVariety, Reliability } from '../domain/playerRecord';
import { countedRows } from '../domain/recordCard';

import { StrandMeterRow } from './StrandMeterRow';
import {
  RECORD_CARD_TITLE_DRAWN,
  VARIETY_LABEL,
  recordCardLabel,
  varietyValue,
} from './recordPresentation';

export interface RecordCardProps {
  /** Absent where nothing has ever fallen due for them. */
  readonly reliability?: Reliability;
  /** A different absence: no counted game has ever been recorded. */
  readonly variety?: OpponentVariety;
}

export function RecordCard({ reliability, variety }: RecordCardProps) {
  const rows = reliability === undefined ? [] : countedRows(reliability.strands);

  // Nothing to say is said by not being here — the same spelling every absence takes on this
  // sheet, and the one that keeps a newcomer's record reading as new rather than as poor.
  if (rows.length === 0 && variety === undefined) return null;

  return (
    <Card>
      <View
        accessible
        accessibilityLabel={recordCardLabel({
          rows,
          ...(variety === undefined ? {} : { variety }),
        })}
      >
        <Text style={s.title}>{RECORD_CARD_TITLE_DRAWN}</Text>

        {rows.map((row, at) => (
          <StrandMeterRow key={row.strand} row={row} divided={at > 0} />
        ))}

        {variety === undefined ? null : (
          <Row
            label={VARIETY_LABEL}
            value={<Text style={s.figure}>{varietyValue(variety)}</Text>}
            divided={rows.length > 0}
          />
        )}
      </View>
    </Card>
  );
}

const s = StyleSheet.create({
  // The eyebrow labels a region you are reading, which is what this heading is; `flab` is for a
  // control you are about to operate and there is none on this card.
  title: { ...theme.type.eyebrow, color: theme.color.muted, marginBottom: theme.space.xs },
  figure: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
});
