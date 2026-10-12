/**
 * ***Who's here*** — the attendance block on a booked game's result screen
 * ([#658](https://github.com/Raketa02/Raketa/issues/658); ADR-0195 §3), one row per player it has
 * something to say about or offer, in the court's order.
 *
 * ```
 * WHO'S HERE
 * Tap for anybody who isn't at the court yet. It works only from the club — …
 * [ Piotr Sowa isn't here yet ]
 * [ Oscar Nowak is here ]                    Oscar is awaited: his arrival is a tap away
 * · Inés Díaz came late
 * ```
 *
 * **One press, and no sheet in front of it.** *Isn't here yet* costs its maker nothing and the
 * arrival lifts it — on time, it vanishes — so there is nothing to confirm; the phone reads where it
 * is at the press, and a refusal is said in the pinned footer beside the screen's other acts. The
 * rows are `domain/attendance.ts`'s; nothing here decides who is on them.
 *
 * Each control is 6.1's `secondary`: the score keeps the one accent while it can be entered, and the
 * reader's own *I'm here* or *I was there*, when offered, is the pinned `primary` — this block is
 * about everybody else. What is said of somebody is the fact list's dotted row, in words.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, theme } from '@/shared/ui';

import type { AttendanceBlock, AttendanceRow } from '../domain/attendance';

import { FactLine } from './FactLine';
import {
  ATTENDANCE_EYEBROW,
  NOT_HERE_YET_LINE,
  SENDING_LABEL,
  attendanceLine,
  attendanceTapLabel,
} from './gamePresentation';

export interface WhosHereProps {
  readonly block: AttendanceBlock;
  /** A row's tap pressed. */
  readonly onTap: (row: AttendanceRow) => void;
  /** The player a tap about is in flight — their control goes busy. */
  readonly tappingAbout?: string;
}

export function WhosHere({ block, onTap, tappingAbout }: WhosHereProps) {
  if (block.rows.length === 0) return null;
  const asksAboutAbsence = block.rows.some((row) => row.tap === 'not-here-yet');

  return (
    <View style={s.block}>
      <Text style={s.eyebrow} accessibilityRole="header">
        {ATTENDANCE_EYEBROW[block.phase]}
      </Text>
      {asksAboutAbsence ? <Text style={s.line}>{NOT_HERE_YET_LINE}</Text> : null}
      {block.rows.map((row) => (
        <View key={row.playerId} style={s.row}>
          {row.said === undefined ? null : <FactLine>{attendanceLine(row.said, row.who)}</FactLine>}
          {row.tap === undefined ? null : (
            <Button
              label={attendanceTapLabel(row.tap, row.who)}
              variant="secondary"
              onPress={() => onTap(row)}
              busy={tappingAbout === row.playerId}
              busyLabel={SENDING_LABEL}
            />
          )}
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  block: { marginTop: theme.space.md, gap: theme.space.xs },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  line: { ...theme.type.tiny, color: theme.color.muted },
  row: { gap: theme.space.xs },
});
