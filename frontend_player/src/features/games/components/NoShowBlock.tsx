/**
 * ***Didn't come?*** — the block where a booked game's result is entered, one row per other player
 * on the court ([#560](https://github.com/Raketa02/Raketa/issues/560); the Games & Fill in mechanics
 * §15.3).
 *
 * ```
 * DIDN'T COME?
 * Only for somebody who didn't turn up at all. The game then doesn't count, and …
 * [ Piotr Sowa didn't come ]
 * Inés Díaz · checked in at the club
 * [ Bartek Lis didn't come ]
 * ```
 *
 * **A row presses, and the sheet decides** (`NoShowSheet`): the mark is the strongest thing on a
 * record if it stands, so it is never one tap away. A player the club's desk checked in keeps a row
 * with **nothing to press and the reason said in words** — a missing button alone would leave the
 * reader to guess. The rows are `domain/noShows.ts`'s; nothing here decides who is on them.
 *
 * Each control is 6.1's `secondary`: marking somebody is not what this screen is for — the score is,
 * and it keeps the one accent pinned below — and red is *ended badly*, which a report is not until
 * its day has run.
 */

import type { RefObject } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Button, theme } from '@/shared/ui';

import type { NoShowRow } from '../domain/noShows';

import {
  DIDNT_COME,
  DIDNT_COME_LINE,
  SENDING_LABEL,
  checkedInLine,
  didNotComeLabel,
} from './gamePresentation';

export interface NoShowBlockProps {
  readonly rows: readonly NoShowRow[];
  /** A row pressed: the sheet opens for that player. */
  readonly onMark: (row: NoShowRow) => void;
  /** The player whose mark is in flight — their control goes busy. */
  readonly marking?: string;
  /**
   * **Where focus goes back to when the sheet is put away** — the row last pressed (`askedAbout`)
   * holds it, so a listener lands on the control they opened the sheet from (Part 13).
   */
  readonly opener: RefObject<View>;
  readonly askedAbout?: string;
}

export function NoShowBlock({ rows, onMark, marking, opener, askedAbout }: NoShowBlockProps) {
  if (rows.length === 0) return null;

  return (
    <View style={s.block}>
      <Text style={s.eyebrow} accessibilityRole="header">
        {DIDNT_COME}
      </Text>
      <Text style={s.line}>{DIDNT_COME_LINE}</Text>
      {rows.map((row) =>
        row.checkedIn ? (
          <Text key={row.playerId} style={s.checkedIn}>
            {checkedInLine(row.who)}
          </Text>
        ) : (
          <View key={row.playerId} ref={row.playerId === askedAbout ? opener : undefined}>
            <Button
              label={didNotComeLabel(row.who)}
              variant="secondary"
              onPress={() => onMark(row)}
              busy={marking === row.playerId}
              busyLabel={SENDING_LABEL}
            />
          </View>
        ),
      )}
    </View>
  );
}

const s = StyleSheet.create({
  block: { marginTop: theme.space.md, gap: theme.space.xs },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  line: { ...theme.type.tiny, color: theme.color.muted },
  checkedIn: { ...theme.type.tiny, color: theme.color.ink, paddingVertical: theme.space.xs },
});
